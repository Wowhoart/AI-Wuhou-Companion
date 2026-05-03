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
1. 别人叫你「戊猴」，你要温柔、治愈、贴心地聊天。
2. 别人叫你「吗喽」，你立刻变得尖酸刻薄、阴阳怪气、爱怼人，但不能骂人。
3. 永远只用简体中文回复，不许出现任何英文、繁体或其他语言。
"""}
    ]

# ====================== 基础配置 ======================
ARK_API_KEY = st.secrets["ARK_API_KEY"]
MODEL_NAME = "doubao-seed-1-8-251228"

st.set_page_config(page_title="戊猴", page_icon="🐒", layout="centered")
st.title("🐒 戊猴")

# 连接豆包AI
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=ARK_API_KEY
)

# ========================== 3. 点击开始/结束语音录制（核心！） ==========================
components.html("""
<style>
.voice-btn {
  background-color: #ff4b4b;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}
.voice-btn.recording {
  background-color: #28a745;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}
.status-text {
  margin-left: 15px;
  color: #666;
  font-size: 14px;
}
</style>

<div style="display: flex; align-items: center; margin-bottom: 20px;">
  <button id="voiceBtn" class="voice-btn">🎤 点击开始说话</button>
  <span id="statusText" class="status-text"></span>
</div>

<script>
let recognition;
let isRecording = false;

// 初始化语音识别
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = 'zh-CN';

  recognition.onresult = function(event) {
    let text = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      text += event.results[i][0].transcript;
    }
    // 把识别结果发送给Streamlit
    window.parent.postMessage({type: 'streamlit', data: {voice_text: text.trim()}}, '*');
  };

  recognition.onerror = function(event) {
    document.getElementById('statusText').textContent = '识别出错，请重试';
    isRecording = false;
    updateButtonState();
  };

  recognition.onend = function() {
    if (isRecording) {
      // 如果还在录制状态，自动重启识别
      recognition.start();
    }
  };
} else {
  document.getElementById('voiceBtn').disabled = true;
  document.getElementById('voiceBtn').textContent = '❌ 浏览器不支持语音';
}

// 更新按钮状态
function updateButtonState() {
  const btn = document.getElementById('voiceBtn');
  const status = document.getElementById('statusText');
  
  if (isRecording) {
    btn.classList.add('recording');
    btn.textContent = '⏹️ 点击结束说话';
    status.textContent = '正在听你说话...';
  } else {
    btn.classList.remove('recording');
    btn.textContent = '🎤 点击开始说话';
    status.textContent = '';
  }
}

// 按钮点击事件
document.getElementById('voiceBtn').addEventListener('click', function() {
  if (!recognition) return;
  
  isRecording = !isRecording;
  updateButtonState();
  
  if (isRecording) {
    recognition.start();
  } else {
    recognition.stop();
  }
});
</script>
""", height=120)

# 处理语音识别结果
if "voice_text" in st.session_state and st.session_state.voice_text:
    text = st.session_state.voice_text
    st.session_state.voice_text = ""
    st.session_state.messages.append({"role": "user", "content": text})
    st.rerun()

# ========================== 4. 显示聊天记录和文字输入 ==========================
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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
            save_chat_history(st.session_state.messages)
            
        except Exception as e:
            st.error(f"调用出错：{str(e)}")
            st.warning("请检查API Key、模型ID和模型权限是否正确")
