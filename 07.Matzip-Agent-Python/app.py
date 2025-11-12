import streamlit as st
from dotenv import load_dotenv
from main import get_agent_response

st.set_page_config(page_title="잠실 맛집 챗봇", page_icon="🤖")

st.title("🤖 잠실 맛집 챗봇")
st.caption("잠실 맛집에 관련된 모든것을 답해드립니다!")

load_dotenv()

if 'message_list' not in st.session_state:
    st.session_state.message_list = []

for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_question := st.chat_input(placeholder="잠실 맛집에 관련된 궁금한 내용들을 말씀해주세요!"):
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.message_list.append({"role": "user", "content": user_question})

    with st.spinner("답변을 생성하는 중입니다"):
        ai_response = get_agent_response(user_question)
        with st.chat_message("ai"):
            st.write(ai_response)
            st.session_state.message_list.append({"role": "ai", "content": ai_response})
