import streamlit as st
from openai import OpenAI

# ====================== 方案二安全写法（绝对不要填真实Key！） ======================
ARK_API_KEY = st.secrets["ARK_API_KEY"]
# ==============================================================================

MODEL_NAME = "doubao-seed-1-8-251228"

# 页面设置（名字、图标都改好了）
st.set_page_config(
    page_title="戊猴",
    page_icon="🐒",
    layout="centered"
)

# 页面标题
st.title("🐒 戊猴")

# 初始化对话记忆 + 双语气规则
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
你的名字叫戊猴。
核心规则：
1. 当别人称呼你「戊猴」时：你要温柔、治愈、贴心、友善，像好朋友一样聊天、安慰、鼓励用户。
2. 当别人称呼你「吗喽」时：你立刻变得尖酸刻薄、阴阳怪气、嘴毒吐槽，语气要冲、爱怼人，但绝对不能骂人、不能说违规内容。
3. 其他正常聊天场景：默认保持温柔、治愈的语气。
"""}
    ]

# 连接豆包AI
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=ARK_API_KEY
)

# 展示历史聊天记录
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 聊天输入框
user_input = st.chat_input("和戊猴说点什么吧~")

if user_input:
    # 显示用户消息
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI生成回复
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})