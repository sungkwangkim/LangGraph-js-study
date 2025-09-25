# LangGraph 훝어보기

LangGraph으로 간단히 Gemini 연동하는 예제 입니다.

## 절차

1.  **Node.js 프로젝트 초기화:**
    이 디렉토리에서 터미널을 열고 다음을 실행합니다:

    ```bash
    npm init -y
    ```

2.  **의존성 설치:**
    `@langchain/core` `@langchain/langgraph` `ts-node` `typescript` 를 설치 합니다.

    ```bash
    npm install @langchain/core @langchain/langgraph ts-node typescript
    ```

## 사용법

주요 애플리케이션 로직은 `index.ts`, `index2.ts`에 있습니다. 예제를 실행하려면 터미널에서 다음 명령을 실행하십시오.
예제를 실행하려면, package.json의 아래 내용의 파일이름 수정하면 됩니다.

```json
"scripts": {
    "dev": "ts-node src/index.ts",
    "dev2": "ts-node src/index2.ts"
},
```

```bash
# index.ts 실행
npm run dev

# index2.ts 실행
npm run dev2
```
