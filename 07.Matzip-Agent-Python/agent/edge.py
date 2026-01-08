from langgraph.graph import END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.documents import Document
from .tool import tools
from .state import GraphState
from pydantic import BaseModel, Field
from typing import Any


def _format_docs_with_metadata(docs: Any) -> str:
    """
    문자열/Document/Document 리스트를 받아 링크·이미지 URL을 포함한 텍스트로 변환합니다.
    """
    if docs is None:
        return ""
    if isinstance(docs, str):
        return docs
    if isinstance(docs, Document):
        docs_iter = [docs]
    else:
        try:
            docs_iter = list(docs)
        except TypeError:
            return str(docs)

    formatted = []
    for idx, doc in enumerate(docs_iter, start=1):
        metadata = getattr(doc, "metadata", {}) or {}
        name = metadata.get("name") or f"문서 {idx}"
        category = metadata.get("category") or ""
        location = metadata.get("location_type") or ""
        reviews = metadata.get("naver_review_count") or ""
        thumbnail = metadata.get("main_thumbnail_url") or ""
        homepage = metadata.get("homepage_url") or ""
        naver_id = metadata.get("naver_id") or ""
        

        lines = [
            f"{idx}. {name}",
            f"카테고리: {category}",
            f"위치: {location}",
            f"네이버 리뷰수: {reviews}",
        ]
        if homepage:
            lines.append(f"홈페이지: {homepage}")
        if naver_id:
            lines.append(f"네이버 지도: https://map.naver.com/p/entry/place/{naver_id}")
        if thumbnail:
            lines.append(f"이미지: {thumbnail}")

        content = getattr(doc, "page_content", "")
        if content:
            lines.append("본문:")
            lines.append(content)

        formatted.append("\n".join([line for line in lines if line.strip()]))

    return "\n\n".join(formatted)

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
    print(messages[0].content)
    print(last_message.content)

    return {"messages": [AIMessage(content=score.binary_score)]}

def check_relevance(state: GraphState) -> str:
    """
    이전 LLM 도구 호출의 관련성을 확인합니다.
    """
    print("---관련성 확인---")
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.content == "yes":
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
    prompt = ChatPromptTemplate.from_template(
        """당신은 음식점 추천 전문가입니다. 아래 context 데이터를 분석하여 사용자에게 최적의 음식점을 추천해주세요.

        고려사항:
        1. 사용자 검색어: {question}
        2. 가격대, 리뷰 수, 위치, 특징을 종합적으로 고려
        3. 사용자 상황(날씨와, 이전에 먹었던 메뉴)에 맞는 추천
        4. metadata에 naver_id가 있으면 네이버 지도 링크를, homepage_url이 있으면 그 링크를 포함하세요.
        5. metadata에 main_thumbnail_url이 있으면 해당 이미지를 함께 제시하세요.

        응답 형식:
        - 1-2개의 최고 추천 음식점 선정
        - 각 음식점의 강점 설명
        - 추천 메뉴 제시
        - 간단한 이유 설명
        - 전체 메뉴와 가격 제시

        context:
        {context}
        ㅡ
        """
    )
    llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)
    rag_chain = prompt | llm
    formatted_context = _format_docs_with_metadata(docs)
    response = rag_chain.invoke({"context": formatted_context, "question": question})

    return {"messages": [response]}



class QuestionRelevance(BaseModel):
    """사용자 질문의 관련성을 평가합니다."""
    is_relevant: str = Field(description="질문이 '음식, 식당 추천'과 관련이 있으면 'yes', 그렇지 않으면 'no'")


def check_question_relevance(state: GraphState) -> GraphState:
    """
    사용자의 질문이 '잠실 음식 및 점심메뉴 추천'과 관련이 있는지 확인합니다.
    """
    print("---질문 관련성 확인---")

    messages = state["messages"]
    question = messages[0].content

    # 이 코드는 사용자 질문에 특정 장소(예: "잠실", "강남" 등)가 언급되었는지 확인합니다.
    # 만약 질문에 장소 정보가 없다면, 기본값으로 "잠실"을 질문 앞에 추가하여
    # 사용자가 특정 장소를 지정하지 않아도 "잠실 맛집"과 관련된 질문으로 처리합니다.
    # 이렇게 함으로써 에이전트가 항상 특정 지역에 대한 맛집 추천을 제공할 수 있도록 합니다.
    # 자주 사용되는 장소 키워드 목록을 정의합니다.
    location_keywords = ["잠실"]

    # 질문에 장소 키워드가 포함되어 있는지 확인합니다.
    has_location = any(keyword in question for keyword in location_keywords)

    # 장소 정보가 없으면 질문 앞에 "잠실"을 추가합니다.
    if not has_location:
        print("---장소 정보 없음: '잠실' 추가---")
        question = "잠실 " + question
        messages[0].content = question # 업데이트된 질문으로 메시지 내용을 갱신합니다.

    prompt = ChatPromptTemplate.from_template(
        """당신은 사용자 질문이 '음식, 식당 추천'과 관련이 있는지 평가하는 평가자입니다.
        다음은 사용자 질문입니다:
        \n ------- \n
        {question}
        \n ------- \n
        질문이 '잠실 음식, 식당 추천'과 관련이 있으면 'yes', 그렇지 않으면 'no'로 평가하세요.
        'yes' 또는 'no'의 이진 점수를 부여하세요."""
    )

    model = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(QuestionRelevance)
    chain = prompt | model
    relevance = chain.invoke({"question": question})
    return {"messages": [AIMessage(content=relevance.is_relevant)]}


def refuse_to_answer(state: GraphState) -> GraphState:
    """
    관련 없는 질문에 대해 답변을 거부하는 메시지를 생성합니다.
    """
    print("---답변 거부---")
    return {"messages": [AIMessage(content="죄송합니다. 저는 잠실 맛집에 대한 질문에만 답변할 수 있습니다.")]}



def decide_on_question_relevance(state: GraphState) -> str:
    """
    'check_question_relevance'의 결과를 바탕으로 분기합니다.
    """
    print("---질문 관련성 분기---")
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.content == "yes":
        print("---결정: 질문 관련 있음---")
        return "yes"

    print("---결정: 질문 관련 없음---")

    return "no"
