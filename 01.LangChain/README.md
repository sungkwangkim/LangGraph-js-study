# LangChain 훝어보기

LangChain으로 간단히 Gemini 연동하는 예제 입니다.

## 절차

1.  **Node.js 프로젝트 초기화:**
    이 디렉토리에서 터미널을 열고 다음을 실행합니다:

    ```bash
    npm init -y
    ```

2.  **의존성 설치:**
    @langchain/core, Google GenAI SDK 및 환경 변수 관리를 위한 dotenv를 설치합니다.

    ```bash
    npm install @langchain/core @langchain/google-genai dotenv
    ```

3.  **환경 변수 설정:**
    이 디렉토리에 `.env`라는 이름의 파일을 만들고 Google API 키를 추가합니다:
    ```
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    ```
    `"YOUR_GOOGLE_API_KEY"`를 실제 API 키로 바꾸십시오.

## 사용법

주요 애플리케이션 로직은 `index.js`에 있습니다. 예제를 실행하려면 터미널에서 다음 명령을 실행하십시오:

```bash
npm run dev
```

그러면 실행이 시작되고 콘솔에서 Gemini 모델의 출력을 볼 수 있습니다.
