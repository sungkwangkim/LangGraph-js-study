# Embedding Model 예제

이 프로젝트는 LangChain.js를 사용하여 Google 및 OpenAI, Upstage의 임베딩 모델을 테스트하기 위해 작성되었습니다.

## 시작하기

프로젝트를 설정하고 필요한 의존성을 설치하려면 다음 단계를 따르세요.

1.  **프로젝트 초기화**

    ```bash
    npm init -y
    ```

2.  **ES 모듈 설정**

    `package.json`에서 type을 "module"로 설정합니다.

    ```bash
    npm pkg set type="module"
    ```

3.  **의존성 설치**

    필요한 라이브러리를 설치합니다.

    ```bash
    npm install @langchain/google-genai @langchain/openai dotenv
    ```

4.  **실행 스크립트 추가**

로컬 실행을 위한 `package.json`에서 `scripts` 코드를 넣습니다.

```json
{
  "name": "04.embeddingmodel",
  "version": "1.0.0",
  "description": "",
  "main": "index.js",
  "scripts": {
    "dev": "node src/index.js"
  },
  "author": "",
  "license": "ISC",
  "type": "module"
}
```

5. **src/index.js 파일 생성**
   04.EmbeddingModel/src/index.js 파일에 있는 내용을 붙여 넣으세요.

6. **실행해 보기**

   터미널에서 커맨드를 입력,

   ```bash
   npm run dev
   ```

   Enter!

## 코드 설명

- `src/index.js`: 메인 실행 파일입니다.
- `sample/king.js`, `sample/koreanKing.js`: Upstage 임베딩 모델의 `curl` 응답을 저장한 샘플 파일입니다.

OpenAI의 `baseURL`을 사용하여 Upstage 임베딩 모델을 직접 호출했을 때, `000, 000`과 같은 비정상적인 응답을 받았습니다. 이 문제를 해결하기 위해 `curl`로 직접 API를 호출하고 그 응답을 샘플 파일로 저장하여 사용했습니다.

```bash
curl --location --request POST 'https://api.upstage.ai/v1/embeddings' \
  --header 'Authorization: Bearer up_c6AhsMfjR4c4M6dDecLaEdRXOJ0gy' \
  --header 'Content-Type: application/json' \
  --data '{
    "input": "king",
    "model": "embedding-query"
  }' > king.json

curl --location --request POST 'https://api.upstage.ai/v1/embeddings' \
  --header 'Authorization: Bearer up_c6AhsMfjR4c4M6dDecLaEdRXOJ0gy' \
  --header 'Content-Type: application/json' \
  --data '{
    "input": "왕",
    "model": "embedding-query"
  }' > koreanKing.json
```

## 결론

- JavaScript 환경에서는 Upstage 임베딩 모델을 직접 사용하기 어려운 점을 확인했습니다. Python에서는 관련 예제가 많고 호환성이 높아 보입니다.
- 향후 임베딩 모델 관련 개발은 Python을 기반으로 진행할 계획입니다.
- LangChain 프레임워크를 사용하면 코드를 훨씬 간결하고 깔끔하게 작성할 수 있다는 장점이 있습니다.
