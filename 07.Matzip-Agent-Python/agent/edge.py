from langgraph.graph import END
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from .tool import tools
from .state import GraphState
from pydantic import BaseModel, Field

# Nodes
def should_retrieve(state: GraphState) -> str:
    """
    에이전트가 더 많은 정보를 검색할지 아니면 프로세스를 종료할지 결정합니다.
    이 함수는 상태의 마지막 메시지에서 함수 호출이 있는지 확인합니다.
    도구 호출이 있으면 정보 검색을 계속하고, 없으면 프로세스를 종료합니다.
    """
    print("---검색 여부 결정---")
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("---결정: 검색 진행---")
        return "retrieve"
    
    return END

class GradeDocuments(BaseModel):
    """검색된 문서에 관련성 점수를 부여합니다."""
    binary_score: str = Field(description="관련성 점수 'yes' 또는 'no'")

def grade_documents(state: GraphState) -> GraphState:
    """
    검색된 문서의 관련성에 따라 에이전트가 계속 진행할지 결정합니다.
    """
    print("---관련성 평가---")
    messages = state["messages"]
    
    prompt = ChatPromptTemplate.from_template(
        """당신은 검색된 문서가 사용자 질문과 관련이 있는지 평가하는 채점자입니다.
        다음은 검색된 문서입니다:
        \n ------- \n
        {context}
        \n ------- \n
        다음은 사용자 질문입니다: {question}
        문서의 내용이 사용자 질문과 관련이 있으면 관련 있음으로 평가하세요.
        문서가 질문과 관련이 있는지 나타내는 'yes' 또는 'no'의 이진 점수를 부여하세요.
        Yes: 문서가 질문과 관련이 있습니다.
        No: 문서가 질문과 관련이 없습니다."""
    )
    
    model = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(GradeDocuments)
    
    chain = prompt | model
    
    last_message = messages[-1]
    
    score = chain.invoke({
        "question": messages[0].content,
        "context": last_message.content,
    })
    
    return {"messages": [AIMessage(content="", tool_calls=[{"name": "give_relevance_score", "args": {"binary_score": score.binary_score}, "id": "0"}])]}

def check_relevance(state: GraphState) -> str:
    """
    이전 LLM 도구 호출의 관련성을 확인합니다.
    """
    print("---관련성 확인---")
    messages = state["messages"]
    last_message = messages[-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        raise ValueError("'check_relevance' 노드는 가장 최근 메시지에 도구 호출이 포함되어야 합니다.")
    
    tool_calls = last_message.tool_calls
    
    if tool_calls[0]["args"]["binary_score"] == "yes":
        print("---결정: 문서 관련 있음---")
        return "yes"
    
    print("---결정: 문서 관련 없음---")
    return "no"

def agent(state: GraphState) -> GraphState:
    """
    현재 상태를 기반으로 응답을 생성하기 위해 에이전트 모델을 호출합니다.
    """
    print("---에이전트 호출---")
    messages = state["messages"]
    
    filtered_messages = [
        message for message in messages
        if not (hasattr(message, "tool_calls") and message.tool_calls and message.tool_calls[0]["name"] == "give_relevance_score")
    ]
    
    model = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True).bind_tools(tools)
    
    response = model.invoke(filtered_messages)
    
    return {"messages": [response]}

def rewrite(state: GraphState) -> GraphState:
    """
    더 나은 질문을 생성하기 위해 쿼리를 변환합니다.
    """
    print("---쿼리 변환---")
    messages = state["messages"]
    question = messages[0].content
    
    prompt = ChatPromptTemplate.from_template(
        """입력을 보고 기본적인 의미나 의도를 파악해보세요. \n
        다음은 초기 질문입니다:
        \n ------- \n
        {question}
        \n ------- \n
        개선된 질문을 작성하세요:"""
    )
    
    model = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)
    
    response = prompt.pipe(model).invoke({"question": question})
    
    return {"messages": [response]}

def generate(state: GraphState) -> GraphState:
    """
a   답변을 생성합니다.
    """
    print("---답변 생성---")
    messages = state["messages"]
    question = messages[0].content
    
    last_tool_message = next((msg for msg in reversed(messages) if msg.type == "tool"), None)
    
    if not last_tool_message:
        raise ValueError("대화 기록에서 도구 메시지를 찾을 수 없습니다")
        
    docs = last_tool_message.content
    
    prompt = Client().pull_prompt("rlm/rag-prompt")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)
    
    rag_chain = prompt | llm
    
    response = rag_chain.invoke({"context": docs, "question": question})
    
    return {"messages": [response]}

