from langgraph.graph import StateGraph, START, END
from .edge import (
    agent,
    grade_documents,
    rewrite,
    generate,
    should_retrieve,
    check_relevance,
    check_question_relevance,
    decide_on_question_relevance,
    refuse_to_answer,
)
from .tool import tool_node
from .state import GraphState

# 그래프 정의
builder = StateGraph(GraphState)

# 순환할 노드들을 정의합니다.
builder.add_node("check_question_relevance", check_question_relevance)
builder.add_node("refuse_to_answer", refuse_to_answer)
builder.add_node("agent", agent)
builder.add_node("retrieve", tool_node)
builder.add_node("grade_documents", grade_documents)
builder.add_node("rewrite", rewrite)
builder.add_node("generate", generate)

builder.add_edge(START, "check_question_relevance")

# 질문 관련성 확인 후 분기
builder.add_conditional_edges(
    "check_question_relevance",
    decide_on_question_relevance,
    {
        "yes": "agent", # 관련이 있다면 바로 agent로 연결
        "no": "refuse_to_answer",
    },
)

builder.add_edge("refuse_to_answer", END)



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
