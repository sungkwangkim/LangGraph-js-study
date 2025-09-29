import { CheerioWebBaseLoader } from "@langchain/community/document_loaders/web/cheerio";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { OpenAIEmbeddings } from "@langchain/openai";
// import { GoogleGenerativeAIEmbeddings } from "@langchain/google-genai";
import dotenv from "dotenv";

dotenv.config();

const urls = [
  "https://blog.naver.com/ban__di/223783862789",
  "https://lazyyellow.tistory.com/87",
  "https://lazyyellow.tistory.com/entry/%EC%9E%A0%EC%8B%A4-%EC%A7%81%EC%9E%A5%EC%9D%B8%EC%9D%B4-%EC%95%8C%EB%A0%A4%EC%A3%BC%EB%8A%94-%EC%9E%A0%EC%8B%A4%EA%B7%BC%EC%B2%98-%EB%A7%9B%EC%A7%91",
];

const docs = await Promise.all(
  urls.map((url) => new CheerioWebBaseLoader(url).load()),
);
const docsList = docs.flat();

const textSplitter = new RecursiveCharacterTextSplitter({
  chunkSize: 500,
  chunkOverlap: 50,
});
const docSplits = await textSplitter.splitDocuments(docsList);

// Add to vectorDB
// const vectorStore = await MemoryVectorStore.fromDocuments(
//   docSplits,
//   new GoogleGenerativeAIEmbeddings(),
// );

const vectorStore = await MemoryVectorStore.fromDocuments(
  docSplits,
  new OpenAIEmbeddings(),
);

export const retriever = vectorStore.asRetriever();