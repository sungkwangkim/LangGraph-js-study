import { CheerioWebBaseLoader } from "@langchain/community/document_loaders/web/cheerio";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";
// import { GoogleGenerativeAIEmbeddings } from "@langchain/google-genai";
import dotenvFlow from 'dotenv-flow';

dotenvFlow.config();

const urls = [
  "https://blog.naver.com/ban__di/223783862789",
  "https://lazyyellow.tistory.com/87",
  "https://funktionalflow.com/%EC%9E%A0%EC%8B%A4-%EB%A7%9B%EC%A7%91/",
];

const docs = await Promise.all(
  urls.map((url) => new CheerioWebBaseLoader(url).load()),
);
const docsList = docs.flat();

// 1. 블로그 글들을 작은 조각(chunk)으로 나눕니다
const textSplitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,
  chunkOverlap: 50,
});
const docSplits = await textSplitter.splitDocuments(docsList);

// console.log("docSplits")
// console.log(docSplits)

// Add to vectorDB
// const vectorStore = await MemoryVectorStore.fromDocuments(
//   docSplits,
//   new GoogleGenerativeAIEmbeddings(),
// );



// 2. 각 텍스트 조각을 벡터(숫자로 된 표현)로 변환하고,
// 메모리 기반 벡터 데이터베이스에 저장합니다.
const vectorStore = await MemoryVectorStore.fromDocuments(
  docSplits,
  new OpenAIEmbeddings(),
);

// 3. 저장된 벡터 데이터베이스를 기반으로 검색기(retriever)를 만듭니다.
export const retriever = vectorStore.asRetriever();