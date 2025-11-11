from langgraph.graph import StateGraph, START, END
from .edge import agent, grade_documents, rewrite, generate, should_retrieve, check_relevance
from .tool import tool_node
from .state import GraphState

# 그래프 정의
builder = StateGraph(GraphState)

# 순환할 노드들을 정의합니다.
builder.add_node("agent", agent)
builder.add_node("retrieve", tool_node)
builder.add_node("grade_documents", grade_documents)
builder.add_node("rewrite", rewrite)
builder.add_node("generate", generate)

builder.add_edge(START, "agent")

# 검색 여부 결정
builder.add_conditional_edges(
    "agent",
    should_retrieve,
)

builder.add_edge("retrieve", "grade_documents")

# grade_documents 노드 이후의 조건부 엣지
builder.add_conditional_edges(
    "grade_documents",
    check_relevance,
    {
        "yes": "generate",
        "no": "rewrite",
    },
)

builder.add_edge("generate", END)
builder.add_edge("rewrite", "agent")

# 그래프 컴파일
graph = builder.compile()
