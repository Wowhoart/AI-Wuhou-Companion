import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components

# ========================== 屏蔽登录弹窗（核心！） ==========================
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
# ============================================================================

# ====================== 安全读取 API KEY ======================
ARK_API_KEY = st.secrets["ARK_API_KEY"]
MODEL_NAME = "doubao-seed-1.8-251228"

# 页面设置
st.set_page_config(
    page_title="戊猴",
    page_icon="🐒",
    layout="centered"
)

# 标题
st.title("🐒 戊猴")

# 对话记忆 + 强制简体中文 + 双语气
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
你的名字叫戊猴，全程必须只用简体中文说话。

规则：
1. 叫你 戊猴 → 温柔、治愈、贴心。
2. 叫你 吗喽 → 立刻变得尖酸刻薄、阴阳怪气、怼人。
3. 永远只用简体中文，不许出现英文。
"""}
    ]

# 连接 AI
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=ARK_API_KEY
)

# 显示聊天记录
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入框
user_input = st.chat_input("和戊猴说点什么吧~")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
