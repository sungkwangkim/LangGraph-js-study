from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components


# 롯데월드 타워 위도 / 경도
LOTTE_WORD_TOWER_LAT = 37.51246909198778
LOTTE_WORD_TOWER_LON =  127.10282686146004

# 위도, 경도 순서로 좌표를 받는다.
LOTTE_WORLD_TOWER_POLYGON: List[Tuple[float, float]] = [
    (37.51322614728272, 127.10032327792408),
    (37.51468881588385, 127.10522128987581),
    (37.5114549924181, 127.10203923668487),
    (37.51321260161727, 127.10590364302612),
]


def _geolocation_component() -> Optional[str]:
    """브라우저의 geolocation API를 호출해 좌표를 받아온다."""
    return components.html(
        """
        <script>
        const sendToStreamlit = (payload) => {
            const json = JSON.stringify(payload);
            Streamlit.setComponentValue(json);
        };

        const success = (pos) => {
            sendToStreamlit({
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
                accuracy: pos.coords.accuracy || null
            });
        };

        const error = (err) => {
            sendToStreamlit({error: err?.message || "위치 정보를 가져오지 못했습니다."});
        };

        if (!navigator.geolocation) {
            error({message: "브라우저가 위치 정보를 지원하지 않습니다."});
        } else {
            navigator.geolocation.getCurrentPosition(success, error, {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 10000
            });
        }
        </script>
        """,
        height=0,
    )


def _point_in_polygon(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
    """Ray casting 알고리즘으로 좌표가 폴리곤 내부인지 확인한다."""
    inside = False
    n = len(polygon)
    for i in range(n):
        lat1, lon1 = polygon[i]
        lat2, lon2 = polygon[(i + 1) % n]
        intersects = (lon1 > lon) != (lon2 > lon)
        if intersects:
            slope = (lat2 - lat1) / (lon2 - lon1 + 1e-12)
            at_lat = slope * (lon - lon1) + lat1
            if lat < at_lat:
                inside = not inside
    return inside


def is_lotte_tower_worker(lat: float, lon: float) -> bool:
    """롯데월드타워 폴리곤 내부인지 여부."""
    return _point_in_polygon(lat, lon, LOTTE_WORLD_TOWER_POLYGON)


def get_user_location() -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    """
    사용자 위치 정보를 가져온다.

    Returns:
        (location, error): location이 dict이면 성공, error가 str이면 실패 메시지.
    """
    if "user_location" in st.session_state:
        return st.session_state["user_location"], None

    raw = _geolocation_component()
    if not raw:
        return None, None

    try:
        payload = json.loads(raw)
    except Exception:
        print("위치 데이터를 해석하지 못했습니다.")
        location = {
            "latitude": LOTTE_WORD_TOWER_LAT,
            "longitude": LOTTE_WORD_TOWER_LON,
        }
        st.session_state["user_location"] = location
        return location, None

    if isinstance(payload, dict) and payload.get("error"):
        return None, str(payload["error"])

    try:
        lat = float(payload.get("lat")) if isinstance(payload, dict) else None
        lon = float(payload.get("lon")) if isinstance(payload, dict) else None
    except Exception:
        return None, "위도/경도 값이 올바르지 않습니다."

    if lat is None or lon is None:
        return None, None

    location = {
        "latitude": lat,
        "longitude": lon,
    }
    st.session_state["user_location"] = location
    return location, None
