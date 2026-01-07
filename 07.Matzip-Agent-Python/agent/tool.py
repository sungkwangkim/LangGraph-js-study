from langchain_classic.tools.retriever import create_retriever_tool
from langgraph.prebuilt import ToolNode
from .retriever import retriever

# 직장인들의 점심 메뉴 관련 정보를 검색합니다.
tool = create_retriever_tool(
    retriever,
    "retrieve_restaurants",
    "잠실 주변의 점심 메뉴를 검색하고 정보를 반환합니다.",
)

# 사용 가능한 모든 도구를 배열로 내보냅니다.
tools = [tool]

# 도구들을 실행할 수 있는 노드를 생성합니다.
# 이 노드는 그래프 상태를 관리하며 도구 호출을 처리합니다.
tool_node = ToolNode(tools)
