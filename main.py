import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder
import json
import base64
import requests
import hmac
import hashlib
import time

# ========================== 屏蔽登录弹窗 ==========================
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

# ========================== 永久保存聊天记录 ==========================
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
"""}
    ]
# ======================================================================

# ========================== 火山引擎签名工具 ==========================
def sign(secret_key, sign_str):
    return hmac.new(secret_key.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).hexdigest()

def get_auth_header(access_key, secret_key, service, region, host, path, method, body):
    timestamp = int(time.time())
    date = time.strftime("%Y%m%d", time.gmtime(timestamp))
    
    credential_scope = f"{date}/{region}/{service}/request"
    signed_headers = "host;x-content-sha256;x-date"
    
    content_sha256 = hashlib.sha256(body.encode('utf-8')).hexdigest()
    
    canonical_request = f"{method}\n{path}\n\nhost:{host}\nx-content-sha256:{content_sha256}\nx-date:{timestamp}\n\n{signed_headers}\n{content_sha256}"
    
    string_to_sign = f"SDK-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    k_date = hmac.new(secret_key.encode('utf-8'), date.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"request", hashlib.sha256).digest()
    
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    authorization = f"SDK-HMAC-SHA256 Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    return {
        "Authorization": authorization,
        "X-Date": str(timestamp),
        "X-Content-Sha256": content_sha256,
        "Content-Type": "application/json"
    }
# ======================================================================

# ========================== 语音识别（HTTP版） ==========================
def audio_to_text(audio_bytes):
    access_key = st.secrets["VOLC_ACCESS_KEY"]
    secret_key = st.secrets["VOLC_SECRET_KEY"]
    
    host = "openspeech.bytedance.com"
    path = "/api/v1/asr/recognize"
    url = f"https://{host}{path}"
    
    body = json.dumps({
        "appid": "volcengine",
        "format": "wav",
        "sample_rate": 16000,
        "language": "zh-CN",
        "audio": base64.b64encode(audio_bytes).decode('utf-8')
    }, ensure_ascii=False)
    
    headers = get_auth_header(access_key, secret_key, "speech", "cn-beijing", host, path, "POST", body)
    
    try:
        resp = requests.post(url, headers=headers, data=body.encode('utf-8'))
        resp_json = resp.json()
        if resp_json.get("code") == 0:
            return resp_json.get("result", {}).get("text", "").strip()
        else:
            return f"语音识别失败：{resp_json.get('message')}"
    except Exception as e:
        return f"语音识别出错：{str(e)}"
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

# ========================== 修正后的语音输入（兼容0.0.8版本） ==========================
st.write("")
col1, col2 = st.columns([1, 5])
with col1:
    # 去掉了不兼容的sample_rate和format参数
    audio = mic_recorder(
        start_prompt="🎤 按住说话",
        stop_prompt="⏹️ 松开发送",
        just_once=True,
        use_container_width=True,
        key="mic_recorder"
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

# 文字输入框
user_input = st.chat_input("和戊猴说点什么吧~")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            
            # 保存聊天记录
            save_chat_history(st.session_state.messages)
            
        except Exception as e:
            st.error(f"调用出错：{str(e)}")
            st.warning("请检查API Key、模型ID和模型权限是否正确")
