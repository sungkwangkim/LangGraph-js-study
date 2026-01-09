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

st.set_page_config(page_title="잠식이", page_icon="🍜")

st.title("🍜 잠식이")
st.caption("당신의 점심을 사랑하는 AI")

load_dotenv()

ALLOWED_INDOOR_LOCATION_TYPES = [
    "롯데월드몰(실내)",
    "롯데백화점(실내)",
    "롯데호텔(실내)",
    "시그니엘(실내)",
    "잠실지하종합상가(실내)",
    "캐슬플라자(실내)",
]


def build_weather_question(weather) -> str:
    """날씨 정보와 근무자 여부에 맞춘 초깃값 질문을 생성."""

    def _temp_group(temp: float) -> str:
        if temp <= 5:
            return "춥다"
        if temp >= 28:
            return "덥다"
        return "적당하다"

    def _precip_type(mm: float) -> str:
        if mm <= 0:
            return "없음"
        if mm < 3:
            return "약한 비"
        if mm < 15:
            return "강한 비"
        return "매우 강한 비"

    def _pm_status(label: str) -> str:
        if "매우나쁨" in label or "매우 나쁨" in label:
            return "매우 나쁨"
        if "나쁨" in label:
            return "나쁨"
        if "보통" in label:
            return "보통"
        if "좋음" in label:
            return "좋음"
        return "확인 불가"

    feels_like = weather.get("feels_like") or weather["temperature"]
    status_parts = [
        f"잠실 현재 기온 {weather['temperature']}℃(체감 {feels_like}℃)",
        f"습도 {int(weather.get('humidity', 0))}%",
        f"강수량 {weather.get('precip_mm', 0)}mm",
        f"풍속 {weather.get('wind_speed', 0)}m/s",
    ]
    if weather.get("description"):
        status_parts.append(weather["description"])

    temp_group = _temp_group(weather["temperature"])
    precip_type = _precip_type(weather.get("precip_mm", 0))
    pm_label, _pm_color = combine_pm(weather.get("pm25"), weather.get("pm10"))
    pm_status = _pm_status(pm_label)
    sky = "맑음" if precip_type == "없음" else "흐림"

    system_prompt = f"""
너는 한국 음식 문화와 직장인 점심/저녁 동선에 매우 익숙한 추천 AI다.
날씨와 체감 환경을 고려하여 음식을 추천하되,
아래 "출력 제약"을 반드시 지켜야 한다.

### 입력 정보
- 온도: "{temp_group}"
- 하늘: "{sky}"
- 바람: "{precip_type}"
- 대기질:"{pm_status}"

### 한국 음식 문화 규칙
1. 비가 오면 전, 칼국수, 수제비, 국물 요리 선호
2. 매우 강한 비나 외출이 힘들면 배달 음식(치킨, 피자, 짬뽕) 선호
3. 추우면 뜨겁고 진한 국물, 고기, 찌개 선호
4. 더우면 냉면, 콩국수, 비빔국수, 치킨, 맥주 선호
5. 미세먼지가 나쁘면 국물 요리, 보양식, 마늘 많은 음식 선호
6. 미세먼지가 매우 나쁘면 외출을 최소화하고 자극적인 실내 음식 선호
4. 날씨가 나쁘면 외부 이동을 최소화함
"""

    base_question = "\n".join(f"- {status}" for status in status_parts)
    question = f"""{system_prompt}


#### 현재 잠실 날씨:
{base_question}

"""

    if needs_indoor(weather):
        allowed_list = "\n".join(f"- {place}" for place in ALLOWED_INDOOR_LOCATION_TYPES)
        question += (
            f"""
            
### 출력 제약 (반드시 준수)
- 추천 음식점은 **실내 이동만 가능한 장소에서만 선택**
- 아래 장소 유형 중에서만 추천할 것
            
[허용 장소 유형 - 이 외는 절대 추천 금지]

{allowed_list}
"""
        )

    return question

location, location_error = get_user_location()
weather, weather_error = fetch_weather()


def render_sources(sources):
    """지도 링크와 썸네일을 카드 형태로 노출합니다."""
    if not sources:
        return

    for src in sources:
        has_thumbnail = bool(src.get("thumbnail"))
        cols = st.columns([1, 2]) if has_thumbnail else [st.container()]

        if has_thumbnail:
            with cols[0]:
                st.image(
                    src["thumbnail"],
                    caption=src.get("name") or "",
                    use_column_width=True,
                )

        with cols[-1]:
            if src.get("name"):
                st.markdown(f"**{src['name']}**")
            if src.get("map_link"):
                st.markdown(f"[네이버 지도 열기]({src['map_link']})")


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

            if needs_indoor(weather):
                st.error("실내 이동 권장 (롯데월드 타워 근무자 기준)")
        else:
            st.info("날씨 정보를 불러오는 중입니다...")

if "message_list" not in st.session_state:
    st.session_state.message_list = []
if "initial_weather_suggestion_done" not in st.session_state:
    st.session_state.initial_weather_suggestion_done = False

if (
    not st.session_state.initial_weather_suggestion_done
    and weather
    and not weather_error
):
    weather_question = build_weather_question(weather)
    st.session_state.message_list.append(
        {"role": "user", "content": weather_question}
    )
    with st.spinner("날씨와 위치에 맞춰 맛집을 추천 중입니다"):
        ai_response = get_agent_response(weather_question)
        if isinstance(ai_response, dict):
            answer = ai_response.get("answer", "")
            sources = ai_response.get("sources") or []
        else:
            answer = ai_response
            sources = []

        st.session_state.message_list.append(
            {"role": "ai", "content": answer, "sources": sources}
        )
    st.session_state.initial_weather_suggestion_done = True

for message in st.session_state.message_list:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        sources = message.get("sources") or []
        print(message.get("sources"))
        render_sources(sources)

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

            render_sources(sources)

            st.session_state.message_list.append(
                {"role": "ai", "content": answer, "sources": sources}
            )
