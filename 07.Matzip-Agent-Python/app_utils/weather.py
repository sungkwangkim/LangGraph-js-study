from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import streamlit as st


@st.cache_data(ttl=300, show_spinner=False)
def fetch_weather() -> Tuple[Optional[Dict], Optional[str]]:
    """한국기상청(잠실 코드) HTML을 파싱해 현재 날씨 정보를 만든다."""
    jamsil_weather_code = "1171071000"
    params = {
        "code": jamsil_weather_code,
        "unit": "m/s",
        "aws": "Y",
    }
    url = "https://www.weather.go.kr/w/wnuri-fct2021/ext/current-weather.do"
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        return None, f"날씨 API 호출 실패: {exc}"

    soup = BeautifulSoup(resp.text, "html.parser")
    container = soup.select_one(".wthema-a")
    if not container:
        return None, "날씨 데이터를 찾지 못했습니다 (.wthema-a)."

    def _first_number(text: str) -> Optional[float]:
        if not text:
            return None
        match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
        return float(match.group()) if match else None

    temp_el = container.select_one(".tmp")
    temp = _first_number(temp_el.get_text(" ", strip=True) if temp_el else "")

    chill_el = container.select_one(".chill")
    feels_like = _first_number(chill_el.get_text(" ", strip=True) if chill_el else "")

    humidity_el = container.find("span", class_="ic-hm")
    humidity = None
    if humidity_el and humidity_el.parent:
        humidity_val = humidity_el.parent.select_one(".val")
        humidity = _first_number(humidity_val.get_text(" ", strip=True) if humidity_val else "")

    wind_el = container.find("span", class_="ic-wind")
    wind_speed = None
    if wind_el and wind_el.parent:
        wind_val = wind_el.parent.select_one(".val")
        wind_speed = _first_number(wind_val.get_text(" ", strip=True) if wind_val else "")

    rain_el = container.find("span", class_="ic-rn")
    precip_mm = 0.0
    if rain_el and rain_el.parent:
        rain_val = rain_el.parent.select_one(".val")
        num = _first_number(rain_val.get_text(" ", strip=True) if rain_val else "")
        precip_mm = num if num is not None else 0.0

    description_el = container.select_one(".w-txt")
    description = description_el.get_text(" ", strip=True) if description_el else ""

    pm25 = None
    pm10 = None
    air_wrap = soup.select_one("ul.air-wrap")
    if air_wrap:
        for item in air_wrap.find_all("li"):
            label_el = item.find("span", class_="lbl")
            label = label_el.get_text(" ", strip=True) if label_el else ""
            value_el = item.select_one(".air-lvv")
            value = _first_number(value_el.get_text(" ", strip=True) if value_el else "")
            if "PM2.5" in label:
                pm25 = value
            elif "PM10" in label:
                pm10 = value

    if temp is None:
        return None, "기온 정보를 파싱하지 못했습니다."

    weather = {
        "temperature": temp,
        "feels_like": feels_like if feels_like is not None else temp,
        "humidity": humidity if humidity is not None else 0,
        "precip_mm": precip_mm,
        # "precip_mm": 30,
        "snow_cm": 0.0,
        "wind_speed": wind_speed if wind_speed is not None else 0.0,
        # "wind_speed": 30,
        "description": description,
        "pm25": pm25,
        "pm10": pm10,
    }
    return weather, None


def needs_indoor(weather: Optional[Dict]) -> bool:
    """롯데타워 근무자가 실내 이동을 권장해야 하는지 여부."""
    if not (weather):
        return False
    rules = [
        weather["precip_mm"] >= 5,
        weather["snow_cm"] >= 5,
        weather["temperature"] >= 33,
        weather["temperature"] <= -6,
        weather["feels_like"] <= -8,
        (weather.get("pm25") or 0) >= 75,
        weather["wind_speed"] >= 9,
    ]
    return any(rules)


def precip_status(mm: Optional[float]) -> Tuple[str, str]:
    """Return (label, color) for precipitation."""
    if mm is None or mm <= 0:
        return "강수 없음", "gray"
    if 1 <= mm < 3:
        return "약한 비", "rgb(92 160 228)"
    if 3 <= mm < 15:
        return "비", "rgb(92, 228, 136)"
    if 15 <= mm < 30:
        return "강한 비", "red"
    return "💀 매우 강한 비", "black"


def pm_status(value: Optional[float], pm_type: str = "pm25") -> Tuple[str, str, int]:
    """Return (label, color, severity) for PM2.5 or PM10."""
    if value is None:
        return "확인 불가", "gray", -1
    thresholds = {
        "pm25": [(0, 15, "미세먼지 좋음"), (16, 35, "미세먼지 보통"), (36, 75, "미세먼지 나쁨"), (76, float("inf"), "미세먼지 매우나쁨")],
        "pm10": [(0, 30, "미세먼지 좋음"), (31, 80, "미세먼지 보통"), (81, 150, "미세먼지 나쁨"), (151, float("inf"), "미세먼지 매우나쁨")],
    }
    for idx, (low, high, label) in enumerate(thresholds[pm_type]):
        if low <= value <= high:
            if label == "미세먼지 매우나쁨":
                return "💀 미세먼지 매우나쁨", "black", 3
            if label in ("미세먼지 좋음", "약한 비"):
                return label, "rgb(92 160 228)", idx
            if label in ("비", "미세먼지 보통"):
                return label, "rgb(92, 228, 136)", idx
            if label in ("강한 비", "미세먼지 나쁨"):
                return label, "red", idx
            return label, "gray", idx
    return "확인 불가", "gray", -1


def combine_pm(pm25: Optional[float], pm10: Optional[float]) -> Tuple[str, str]:
    """Combine PM2.5/PM10 into a single label based on the worse severity."""
    label25, color25, sev25 = pm_status(pm25, pm_type="pm25")
    label10, color10, sev10 = pm_status(pm10, pm_type="pm10")
    if sev25 == -1 and sev10 == -1:
        return "확인 불가", "gray"
    if sev25 >= sev10:
        return label25, color25
    return label10, color10


def wind_status(speed: Optional[float]) -> Tuple[str, str]:
    """Return (label, color) for wind speed."""
    if speed is None:
        return "확인 불가", "gray"
    if 0 <= speed < 4:
        return "바람 없음", "rgb(92 160 228)"
    if 4 <= speed < 9:
        return "약한 바람", "rgb(92 160 228)"
    if 9 <= speed < 14:
        return "강한 바람", "rgb(92, 228, 136)"
    if 14 <= speed < 21:
        return "매우 강한 바람", "red"
    return "💀 강풍경보", "black"


def colored_label(label: str, color: str) -> str:
    """색상과 강조를 적용한 HTML 스팬."""
    return f"<span style='color:{color}; font-weight:700'>{label}</span>"
