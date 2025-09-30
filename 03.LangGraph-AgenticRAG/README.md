# LangGraph.js를 이용한 Agentic RAG 예제

이 예제는 LangGraph.js를 사용하여 Agentic RAG(Retrieval-Augmented Generation)를 구현하는 방법을 보여줍니다. 이 가이드를 통해 단계별로 예제를 설정하고 실행하는 방법을 배울 수 있습니다.

## Agentic RAG란?

Agentic RAG는 검색된 정보를 사용하여 답변을 생성하는 RAG 모델에 에이전트의 개념을 결합한 것입니다. 에이전트는 **동적**으로 검색을 수행하고, 검색된 정보의 **관련성을 평가**하며, 필요한 경우 **쿼리를 다시 작성**하여 **더 나은 답변**을 생성합니다.

이 예제에서는 다음 단계를 통해 Agentic RAG를 구현합니다.

1.  **검색(Retrieve):** 사용자의 질문과 관련된 정보를 미리 정의된 블로그 게시물에서 검색합니다.
2.  **관련성 평가(Grade):** 검색된 문서가 질문과 관련이 있는지 평가합니다.
3.  **쿼리 재작성(Rewrite):** 관련성이 낮은 경우, 더 나은 검색 결과를 얻기 위해 질문을 다시 작성합니다.
4.  **답변 생성(Generate):** 관련성이 높은 경우, 검색된 정보를 바탕으로 최종 답변을 생성합니다.

## 사전 준비

이 예제를 실행하려면 다음이 필요합니다.

- [Node.js](https://nodejs.org/) (버전 18 이상)
- 텍스트 에디터 (예: Visual Studio Code)
- OpenAI API 키

## 설정 및 설치

1.  **저장소 복제:**

    ```bash
    git clone https://github.com/your-username/LangGraph-js-study.git
    cd 03.LangGraph-AgenticRAG
    ```

2.  **의존성 설치:**

    ```bash
    npm install
    ```

3.  **환경 변수 설정:**

    `.env` 파일을 생성하고 다음과 같이 OpenAI API 키를 추가합니다.

    ```
    OPENAI_API_KEY="your-openai-api-key"
    ```

## 예제 실행

다음 명령어를 사용하여 예제를 실행합니다.

```bash
npm run dev
```

실행하면 콘솔에 다음과 같은 출력이 표시됩니다.

```
---에이전트 호출---
---검색 여부 결정---
---결정: 검색 진행---
---관련성 평가---
---관련성 확인---
---결정: 문서 관련 있음---
---답변 생성---
{ "messages": [ ... ] }
```

## 코드 설명

이 예제의 핵심 코드는 `src/agent` 디렉토리에 있습니다.

- **`graph.ts`:** LangGraph를 사용하여 에이전트의 워크플로우를 정의합니다. 각 노드와 엣지는 특정 작업을 수행합니다.
- **`edge.ts`:** 그래프의 각 노드(예: `agent`, `gradeDocuments`, `generate`)와 조건부 엣지(예: `shouldRetrieve`, `checkRelevance`)의 로직을 구현합니다.
- **`tool.ts`:** 에이전트가 사용할 수 있는 도구를 정의합니다. 이 예제에서는 블로그 게시물을 검색하는 `retriever` 도구를 사용합니다.
- **`retriever.ts`:** `CheerioWebBaseLoader`를 사용하여 웹 페이지를 로드하고, `MemoryVectorStore`에 저장하여 검색 가능한 리트리버를 생성합니다.

## 사용자 정의

이 예제를 자신의 용도에 맞게 수정할 수 있습니다.

- **다른 블로그 게시물 사용:** `src/agent/retriever.ts` 파일의 `urls` 배열을 수정하여 다른 블로그 게시물을 사용하도록 변경할 수 있습니다.
- **프롬프트 수정:** `src/agent/edge.ts` 파일의 프롬프트를 수정하여 에이전트의 행동을 변경할 수 있습니다.
- **다른 언어 모델 사용:** `ChatOpenAI` 대신 다른 언어 모델(예: `ChatGoogleGenerativeAI`)을 사용하도록 코드를 수정할 수 있습니다.

## 결론

이 예제를 통해 LangGraph.js를 사용하여 Agentic RAG를 구현하는 방법을 배웠습니다. Agentic RAG는 동적인 정보 검색과 생성을 통해 더 정확하고 관련성 높은 답변을 제공하는 강력한 패러다임입니다.
