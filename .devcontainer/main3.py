import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components

# 屏蔽登录弹窗
components.html("""
<script>
window.addEventListener('load',function(){setTimeout(()=>{
document.querySelectorAll('.st-modal,.st-overlay').forEach(el=>el.remove())
},100)})
</script>
""",height=0)

# 安全读取API Key
ARK_API_KEY = st.secrets["ARK_API_KEY"]
MODEL_NAME = "doubao-seed-1-8-251228"

# 页面设置
st.set_page_config(
    page_title="戊猴",
    page_icon="🐒",
    layout="centered"
)

st.title("🐒 戊猴")

# 核心人设：以文章内容为基础，分享CSA酒店经验
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": """
你叫戊猴，你已经认真学习了这篇关于泰国Sampran Riverside Hotel社区支持农业（CSA）的案例文章：
https://www.pcd.org.hk/csa/gb/experience05-4.html

你现在的唯一任务，就是向询问者分享、讲解、介绍这篇文章里的内容，就像一个有经验的分享者一样。
你要做到：
1. 所有回答都**严格基于文章内容**，只说里面提到的信息、经验、做法和案例，不编造、不延伸文章以外的知识。
2. 语气要亲切、像朋友分享经验一样，可以用轻松易懂的语言解释CSA模式、酒店的做法、社区支持农业的价值。
3. 当用户问的问题和这篇文章无关时，你要礼貌说明：「我目前只专注分享这篇关于泰国CSA酒店的案例经验，其他问题暂时无法回答哦。」
4. 全程使用简体中文，语言自然流畅。
"""
    }]

# 连接火山方舟API
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=ARK_API_KEY
)

# 展示聊天记录
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 聊天输入框
user_input = st.chat_input("来聊聊这篇泰国CSA酒店的案例吧~")

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