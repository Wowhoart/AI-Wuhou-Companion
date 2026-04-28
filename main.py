import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components

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
# ==================================================================

# ====================== 安全读取 API KEY ======================
ARK_API_KEY = st.secrets["ARK_API_KEY"]
# 修正模型ID，必须和火山方舟控制台里的完全一致
MODEL_NAME = "doubao-seed-1-8-251228"

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
1. 别人叫你「戊猴」，你要温柔、治愈、贴心地聊天。
2. 别人叫你「吗喽」，你立刻变得尖酸刻薄、阴阳怪气、爱怼人，但不能骂人。
3. 永远只用简体中文回复，不许出现任何英文、繁体或其他语言。
"""}
    ]

# 连接火山方舟API（地址固定不变）
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=ARK_API_KEY
)

# 显示聊天记录
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 聊天输入框
user_input = st.chat_input("和戊猴说点什么吧~")

if user_input:
    st.chat_message("user").markdown(user_input)
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
        except Exception as e:
            st.error(f"调用出错：{str(e)}")
            st.warning("请检查API Key、模型ID和模型权限是否正确")
