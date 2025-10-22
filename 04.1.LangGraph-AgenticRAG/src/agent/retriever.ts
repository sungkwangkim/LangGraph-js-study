import { Chroma } from "@langchain/community/vectorstores/chroma";
import { OpenAIEmbeddings } from "@langchain/openai";
import dotenvFlow from 'dotenv-flow';

dotenvFlow.config();

// 2. 각 텍스트 조각을 벡터(숫자로 된 표현)로 변환하고,
// 메모리 기반 벡터 데이터베이스에 저장합니다.
const vectorStore = await Chroma.fromExistingCollection(
  new OpenAIEmbeddings(),
  {
    collectionName: "a-test-collection",
    url: "http://localhost:8000",
  },
);

// 3. 저장된 벡터 데이터베이스를 기반으로 검색기(retriever)를 만듭니다.
export const retriever = vectorStore.asRetriever();