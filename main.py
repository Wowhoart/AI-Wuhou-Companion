import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder
import json
import base64
from volcengine.ApiInfo import ApiInfo
from volcengine.Credentials import Credentials
from volcengine.ServiceInfo import ServiceInfo
from volcengine.base.Service import Service

# ========================== 1. 屏蔽登录弹窗 ==========================
components.html("""
<script>
window.addEventListener('load', function() {
  setTimeout(() => {
    const loginOverlay = document.querySelector('.st-eb');
    const loginModal = document.querySelector('.st-ci');
    if (loginOverlay) loginOverlay.remove();
    if (loginModal) loginModal.remove();
    document.body.style.overflow = 'auto';
  }, 100);
});
</script>
""", height=0, width=0)
# ======================================================================

# ========================== 2. 永久保存聊天记录 ==========================
def save_chat_history(messages):
    save_messages = [msg for msg in messages if msg["role"] != "system"]
    history_json = json.dumps(save_messages, ensure_ascii=False)
    components.html(f"""
    <script>
    localStorage.setItem('wuhou_chat_history', '{history_json}');
    </script>
    """, height=0, width=0)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
你的名字叫戊猴，全程必须只用简体中文说话。

规则：
1. 别人叫你「戊猴」，你要温柔、治愈、贴心地聊天。
2. 别人叫你「吗喽」，你立刻变得尖酸刻薄、阴阳怪气、爱怼人，但不能骂人。
3. 永远只用简体中文回复，不许出现任何英文、繁体或其他语言。
4. 回复要简洁自然，适合语音播报，不要太长。
"""}
    ]
    
    load_script = """
    <script>
    const history = localStorage.getItem('wuhou_chat_history');
    if (history) {
      window.parent.postMessage({type: 'load_history', data: history}, '*');
    }
    </script>
    """
    components.html(load_script, height=0, width=0)
# ======================================================================

# ========================== 3. 火山引擎语音识别初始化 ==========================
@st.cache_resource
def init_volc_asr():
    service_info = ServiceInfo(
        "openspeech.bytedance.com",
        {"Content-Type": "application/json"},
        Credentials(
            st.secrets["VOLC_ACCESS_KEY"],
            st.secrets["VOLC_SECRET_KEY"],
            "speech",
            "cn-beijing"
        ),
        5,
        5
    )
    api_info = {
        "AsrRecognize": ApiInfo(
            "POST",
            "/api/v1/asr/recognize",
            {},
            {},
            {}
        )
    }
    service = Service(service_info, api_info)
    return service

def audio_to_text(audio_bytes):
    service = init_volc_asr()
    body = {
        "appid": "volcengine",
        "format": "wav",
        "sample_rate": 16000,
        "language": "zh-CN",
        "audio": base64.b64encode(audio_bytes).decode('utf-8')
    }
    try:
        resp = service.json("AsrRecognize", {}, body)
        if resp.get("code") == 0:
            return resp.get("result", {}).get("text", "").strip()
        else:
            return f"语音识别失败：{resp.get('message')}"
    except Exception as e:
        return f"语音识别出错：{str(e)}"
# ======================================================================

# ========================== 4. 火山引擎语音合成初始化（新增！） ==========================
@st.cache_resource
def init_volc_tts():
    service_info = ServiceInfo(
        "openspeech.bytedance.com",
        {"Content-Type": "application/json"},
        Credentials(
            st.secrets["VOLC_ACCESS_KEY"],
            st.secrets["VOLC_SECRET_KEY"],
            "speech",
            "cn-beijing"
        ),
        5,
        5
    )
    api_info = {
        "TtsSynthesize": ApiInfo(
            "POST",
            "/api/v1/tts/synthesize",
            {},
            {},
            {}
        )
    }
    service = Service(service_info, api_info)
    return service

def text_to_audio(text):
    service = init_volc_tts()
    body = {
        "appid": "volcengine",
        "text": text,
        "voice_type": "BV001_streaming",  # 温柔女声，适合戊猴人设
        "format": "mp3",
        "sample_rate": 16000,
        "speed": 1.0,
        "volume": 1.0
    }
    try:
        resp = service.json("TtsSynthesize", {}, body)
        if resp.get("code") == 0:
            audio_base64 = resp.get("result", {}).get("audio", "")
            return base64.b64decode(audio_base64)
        else:
            return None
    except Exception as e:
        return None
# ======================================================================

# ====================== 基础配置 ======================
ARK_API_KEY = st.secrets["ARK_API_KEY"]
MODEL_NAME = "doubao-seed-1-8-251228"

st.set_page_config(
    page_title="戊猴",
    page_icon="🐒",
    layout="centered"
)

st.title("🐒 戊猴")

# 连接豆包AI
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=ARK_API_KEY
)

# ========================== 5. 全自动语音输入 ==========================
st.write("")
col1, col2 = st.columns([1, 5])
with col1:
    audio = mic_recorder(
        start_prompt="🎤 按住说话",
        stop_prompt="⏹️ 松开发送",
        just_once=True,
        use_container_width=True,
        key="mic_recorder",
        format="wav",
        sample_rate=16000
    )

if audio and "bytes" in audio:
    with st.spinner("🎤 正在转文字..."):
        text = audio_to_text(audio["bytes"])
    
    if text and not text.startswith("语音识别"):
        st.session_state.messages.append({"role": "user", "content": text})
        st.rerun()
    else:
        st.error(text)
# ======================================================================

# 显示聊天记录
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 如果是AI的回复，显示语音播放按钮
        if msg["role"] == "assistant" and "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# 文字输入框
user_input = st.chat_input("和戊猴说点什么吧~")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# AI生成回复 + 自动语音合成
if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            
            # 自动生成语音回复
            with st.spinner("🔊 正在生成语音..."):
                audio_bytes = text_to_audio(reply)
            
            if audio_bytes:
                # 显示语音播放按钮，并自动播放
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                # 把语音和文字一起保存到聊天记录
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "audio": audio_bytes
                })
            else:
                st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # 保存聊天记录
            save_chat_history(st.session_state.messages)
            
        except Exception as e:
            st.error(f"调用出错：{str(e)}")
            st.warning("请检查API Key、模型ID和模型权限是否正确")
