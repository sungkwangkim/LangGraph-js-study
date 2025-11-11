from typing import List, Annotated, TypedDict
from langchain_core.messages import BaseMessage
import operator

# Annotated를 사용하여 상태의 각 필드에 대한 리듀서 함수를 정의합니다.
# operator.add는 메시지를 리스트에 추가하는 역할을 합니다.
# 이는 상태가 업데이트될 때 메시지가 누적되도록 합니다.
class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
