import ast
import re
from typing import Any, Dict, List, Optional

from agent.graph import graph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document


def _build_source(meta: Dict[str, Any]) -> Optional[Dict[str, str]]:
    name = meta.get("name") or ""
    homepage = meta.get("homepage_url") or ""
    naver_id = meta.get("naver_id") or ""
    naver_map_link = f"https://map.naver.com/p/entry/place/{naver_id}" if naver_id else ""
    map_link = naver_map_link or homepage
    thumbnail = meta.get("main_thumbnail_url") or ""

    if not (map_link or thumbnail):
        return None

    return {
        "name": name,
        "map_link": map_link,
        "thumbnail": thumbnail,
    }


def _parse_metadata_from_str(raw: str) -> List[Dict[str, Any]]:
    """
    ToolMessage.content가 문자열인 경우, repr에 포함된 metadata={}를 파싱합니다.
    """
    metadatas: List[Dict[str, Any]] = []
    for match in re.finditer(r"metadata=({.*?})", raw, re.DOTALL):
        text = match.group(1)
        try:
            meta = ast.literal_eval(text)
        except Exception:
            continue
        if isinstance(meta, dict):
            metadatas.append(meta)
    return metadatas


def _extract_sources_from_result(docs: Any) -> List[Dict[str, str]]:
    """문서 메타데이터에서 지도 링크와 썸네일을 뽑아냅니다."""
    if docs is None:
        return []

    metadatas: List[Dict[str, Any]] = []

    if isinstance(docs, Document):
        metadatas.append(getattr(docs, "metadata", {}) or {})
    elif isinstance(docs, str):
        metadatas.extend(_parse_metadata_from_str(docs))
    else:
        try:
            docs_iter = list(docs)
        except TypeError:
            docs_iter = []

        for doc in docs_iter:
            if isinstance(doc, Document):
                metadatas.append(getattr(doc, "metadata", {}) or {})
            elif isinstance(doc, dict):
                # allow dict or {"metadata": {...}}
                meta = doc.get("metadata") if "metadata" in doc else doc
                if isinstance(meta, dict):
                    metadatas.append(meta)
            elif isinstance(doc, str):
                metadatas.extend(_parse_metadata_from_str(doc))

    sources = []
    for meta in metadatas:
        src = _build_source(meta)
        if src:
            sources.append(src)

    return sources

def get_agent_response(message: str):
    initial_state = {
        "messages": [HumanMessage(content=message)],
    }
    try:
        result = graph.invoke(initial_state)
        # The final response is in the last AIMessage of the 'messages' list
        final_response = next(
            (m.content for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content),
            "Sorry, I couldn't find an answer.",
        )
        # 마지막 도구 호출에서 메타데이터를 추출해 지도 링크/썸네일을 함께 반환
        last_tool_message = next(
            (m for m in reversed(result["messages"]) if getattr(m, "type", "") == "tool"),
            None,
        )
        sources = _extract_sources_from_result(getattr(last_tool_message, "content", None))

        return {"answer": final_response, "sources": sources}
    except Exception as e:
        print(f"Error: {e}")
        return f"An error occurred: {e}"
