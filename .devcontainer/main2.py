import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import datetime
import pandas as pd

# ========================== 强制屏蔽登录弹窗 ==========================
components.html("""
<script>
window.addEventListener('load', function() {
  setTimeout(() => {
    const overlay = document.querySelector('.st-eb');
    const modal = document.querySelector('.st-ci');
    if (overlay) overlay.remove();
    if (modal) modal.remove();
    document.body.style.overflow = 'auto';
  }, 100);
});
</script>
""", height=0, width=0)

# ========================== 手机弹窗提醒函数 ==========================
def show_phone_alert(message):
    components.html(f"""
    <script>
        alert("⚠️ 情绪风险提醒：\\n{message}");
    </script>
    """, height=0, width=0)

# ========================== 初始化会话状态 ==========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": """
你的名字叫戊猴，全程只说简体中文。

规则：
1. 别人叫你「戊猴」，你要温柔、治愈、贴心地聊天。
2. 别人叫你「吗喽」，你立刻变得尖酸刻薄、阴阳怪气、爱怼人，但不能骂人。
3. 永远只用简体中文回复，不许出现英文。
"""}
    ]

# 情绪报告数据
if "emotion_log" not in st.session_state:
    st.session_state.emotion_log = []

# ========================== API 配置 ==========================
ARK_API_KEY = st.secrets["ARK_API_KEY"]
MODEL_NAME = "doubao-seed-1-8-251228"

# ========================== 页面设置 ==========================
st.set_page_config(page_title="戊猴", page_icon="🐒", layout="centered")
st.title("🐒 戊猴")

# ========================== 情绪识别函数 ==========================
def analyze_emotion(text):
    """AI+关键词双重情绪识别"""
    text = text.lower()
    # 高危关键词
    risk_keywords = ["想死", "不想活", "活不下去", "自杀", "自残", "绝望", "撑不下去", "好累想消失"]
    sad_keywords = ["难过", "不开心", "委屈", "想哭", "压力大", "累", "烦"]
    happy_keywords = ["开心", "快乐", "喜欢", "太棒了", "幸福", "好爽"]
    anxious_keywords = ["焦虑", "紧张", "担心", "害怕", "睡不着", "心慌"]

    # 先判断高危
    for kw in risk_keywords:
        if kw in text:
            return "高危", f"检测到高危情绪：用户提到「{kw}」，请立即关心！", 1
    # 再判断其他情绪
    if any(kw in text for kw in happy_keywords):
        return "开心", "", 5
    elif any(kw in text for kw in sad_keywords):
        return "难过", "", 3
    elif any(kw in text for kw in anxious_keywords):
        return "焦虑", "", 2
    else:
        return "正常", "", 4

# ========================== 聊天界面 ==========================
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("和戊猴说点什么吧~")

if user_input:
    # 显示用户消息
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 情绪识别 + 日志记录
    emotion, warn_msg, score = analyze_emotion(user_input)
    now = datetime.datetime.now().strftime("%H:%M")
    st.session_state.emotion_log.append({
        "time": now,
        "emotion": emotion,
        "score": score
    })

    # 高危情绪弹窗提醒
    if warn_msg:
        show_phone_alert(warn_msg)
        st.warning(warn_msg)

    # AI回复
    with st.chat_message("assistant"):
        client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=ARK_API_KEY
        )
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# ========================== 情绪日报卡片 ==========================
if st.session_state.emotion_log:
    st.divider()
    st.subheader("📊 今日情绪报告")
    df = pd.DataFrame(st.session_state.emotion_log)

    # 情绪统计
    emotion_counts = df["emotion"].value_counts().to_dict()
    avg_score = round(df["score"].mean(), 1)

    # 报告卡片
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="今日平均心情指数", value=f"{avg_score}/5", delta=None)
    with col2:
        st.metric(label="对话次数", value=len(df), delta=None)

    # 情绪分布
    st.write("今日情绪分布：")
    for emo, cnt in emotion_counts.items():
        if emo == "高危":
            st.error(f"⚠️ {emo}: {cnt}次")
        elif emo == "难过":
            st.warning(f"😔 {emo}: {cnt}次")
        elif emo == "焦虑":
            st.info(f"😰 {emo}: {cnt}次")
        elif emo == "开心":
            st.success(f"😊 {emo}: {cnt}次")
        else:
            st.write(f"😐 {emo}: {cnt}次")

    # 情绪趋势图
    st.line_chart(df.set_index("time")["score"], use_container_width=True)
    st.caption("心情指数趋势（1=高危/很低 5=开心/很高）")