import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import json

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
"""}
    ]
# ======================================================================

# ========================== 3. 浏览器原生语音识别（核心！零依赖） ==========================
components.html("""
<script>
let recognition;
let isListening = false;

// 初始化语音识别
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'zh-CN';

  recognition.onresult = function(event) {
    const text = event.results[0][0].transcript;
    // 把识别结果发送给Streamlit
    window.parent.postMessage({type: 'voice_input', data: text}, '*');
  };

  recognition.onerror = function(event) {
    window.parent.postMessage({type: 'voice_error', data: event.error}, '*');
  };
}

// 监听Streamlit发来的消息
window.addEventListener('message', function(event) {
  if (event.data.type === 'start_listening') {
    if (recognition && !isListening) {
      recognition.start();
      isListening = true;
    }
  } else if (event.data.type === 'stop_listening') {
    if (recognition && isListening) {
      recognition.stop();
      isListening = false;
    }
  }
});
</script>
""", height=0, width=0)

# 语音输入按钮和状态
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

if "is_listening" not in st.session_state:
    st.session_state.is_listening = False

st.write("")
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🎤 按住说话", use_container_width=True, type="primary"):
        st.session_state.is_listening = True
        components.html("""
        <script>
        window.parent.postMessage({type: 'start_listening'}, '*');
        </script>
        """, height=0, width=0)
        st.rerun()

# 处理语音识别结果
if st.session_state.is_listening:
    st.info("正在听你说话...")
    # 等待语音识别结果
    components.html("""
    <script>
    window.addEventListener('message', function(event) {
      if (event.data.type === 'voice_input') {
        window.parent.postMessage({type: 'streamlit', data: {voice_text: event.data.data}}, '*');
      } else if (event.data.type === 'voice_error') {
        window.parent.postMessage({type: 'streamlit', data: {voice_error: event.data.data}}, '*');
      }
    });
    </script>
    """, height=0, width=0)
    
    # 检查是否有结果
    if st.session_state.voice_text:
        text = st.session_state.voice_text
        st.session_state.voice_text = ""
        st.session_state.is_listening = False
        st.session_state.messages.append({"role": "user", "content": text})
        st.rerun()
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
