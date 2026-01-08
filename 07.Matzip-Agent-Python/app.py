import streamlit as st
from dotenv import load_dotenv

from app_utils.location import get_user_location, is_lotte_tower_worker
from app_utils.weather import (
    colored_label,
    combine_pm,
    fetch_weather,
    needs_indoor,
    precip_status,
    wind_status,
)
from main import get_agent_response

st.set_page_config(page_title="잠실 맛집 챗봇", page_icon="🤖")

st.title("🤖 잠실 맛집 챗봇")
st.caption("잠실 맛집에 관련된 모든것을 답해드립니다!")

load_dotenv()

location, location_error = get_user_location()
weather, weather_error = fetch_weather()

is_employee = bool(location) and is_lotte_tower_worker(
    location["latitude"], location["longitude"]
)

with st.container():
    st.subheader("현재 정보")
    col_loc, col_weather = st.columns(2)

    with col_loc:
        st.markdown("**위치 정보**")
        if location_error:
            st.warning(location_error)
        elif location:
            lat = location["latitude"]
            lon = location["longitude"]
            if is_employee:
                st.success("롯데월드 타워 근무자")
            else:
                st.info("위치 확인됨")
            st.text(f"위도: {lat:.5f}, 경도: {lon:.5f}")
            if location.get("accuracy") is not None:
                st.caption(f"정확도 ±{location['accuracy']:.0f} m")
        else:
            st.info("브라우저 위치 권한을 허용해 주세요.")

    with col_weather:
        st.markdown("**잠실 현재 날씨**")
        if weather_error:
            st.warning(weather_error)
        elif weather:
            feels_like = weather.get("feels_like")
            if feels_like is not None:
                st.markdown(
                    f"<div style='font-size:2.6rem;font-weight:700'>"
                    f"{weather['temperature']}℃ "
                    f"<span style='font-size:1.8rem;font-weight:600;opacity:0.8'>(체감 {feels_like}℃)</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.metric("기온", f"{weather['temperature']}℃")
            precip_label, precip_color = precip_status(weather.get("precip_mm"))
            wind_label, wind_color = wind_status(weather.get("wind_speed"))
            pm_label, pm_color = combine_pm(weather.get("pm25"), weather.get("pm10"))

            st.markdown(
                " / ".join(
                    [
                        f"습도 {int(weather['humidity'])}%",
                        colored_label(precip_label, precip_color),
                        colored_label(wind_label, wind_color),
                        colored_label(pm_label, pm_color),
                    ]
                ),
                unsafe_allow_html=True,
            )
            if weather.get("description"):
                st.caption(weather["description"])

            if needs_indoor(weather, is_employee):
                st.error("실내 이동 권장 (롯데월드 타워 근무자 기준)")
        else:
            st.info("날씨 정보를 불러오는 중입니다...")

if "message_list" not in st.session_state:
    st.session_state.message_list = []

for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        sources = message.get("sources") or []
        if sources:
            for src in sources:
                cols = st.columns([1, 2]) if src.get("thumbnail") else [st.container()]
                if src.get("thumbnail"):
                    with cols[0]:
                        st.image(src["thumbnail"], caption=src.get("name") or "", use_column_width=True)
                    with cols[1]:
                        if src.get("name"):
                            st.markdown(f"**{src['name']}**")
                        if src.get("map_link"):
                            st.markdown(f"[지도 보기]({src['map_link']})")
                else:
                    if src.get("name"):
                        st.markdown(f"**{src['name']}**")
                    if src.get("map_link"):
                        st.markdown(f"[지도 보기]({src['map_link']})")

if user_question := st.chat_input(placeholder="잠실 맛집에 관련된 궁금한 내용들을 말씀해주세요!"):
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.message_list.append({"role": "user", "content": user_question})

    with st.spinner("답변을 생성하는 중입니다"):
        ai_response = get_agent_response(user_question)
        with st.chat_message("ai"):
            if isinstance(ai_response, dict):
                answer = ai_response.get("answer", "")
                sources = ai_response.get("sources") or []
            else:
                answer = ai_response
                sources = []

            st.write(answer)

            if sources:
                for src in sources:
                    cols = st.columns([1, 2]) if src.get("thumbnail") else [st.container()]
                    if src.get("thumbnail"):
                        with cols[0]:
                            st.image(src["thumbnail"], caption=src.get("name") or "", use_column_width=True)
                        with cols[1]:
                            if src.get("name"):
                                st.markdown(f"**{src['name']}**")
                            if src.get("map_link"):
                                st.markdown(f"[지도 보기]({src['map_link']})")
                    else:
                        if src.get("name"):
                            st.markdown(f"**{src['name']}**")
                        if src.get("map_link"):
                            st.markdown(f"[지도 보기]({src['map_link']})")

            st.session_state.message_list.append(
                {"role": "ai", "content": answer, "sources": sources}
            )
