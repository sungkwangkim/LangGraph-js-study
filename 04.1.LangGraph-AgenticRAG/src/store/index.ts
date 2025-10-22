import { CheerioWebBaseLoader } from "@langchain/community/document_loaders/web/cheerio";
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { OpenAIEmbeddings } from "@langchain/openai";
import dotenvFlow from "dotenv-flow";

dotenvFlow.config();

export async function runIndexing() {
  const urls = [
  "https://blog.naver.com/PostView.naver?blogId=ban__di&logNo=223783862789&redirect=Dlog&widgetTypeCall=true&noTrackingCode=true&directAccess=false",
  "https://lazyyellow.tistory.com/87",
  "https://funktionalflow.com/%EC%9E%A0%EC%8B%A4-%EB%A7%9B%EC%A7%91/",
];

  console.log("📥 [Indexing] Loading documents...");

  const docs = await Promise.all(urls.map((url) => new CheerioWebBaseLoader(url).load()));
  const docsList = docs.flat();

  const textSplitter = new RecursiveCharacterTextSplitter({
    chunkSize: 500,
    chunkOverlap: 50,
  });
  const docSplits = await textSplitter.splitDocuments(docsList);

  console.log(`🧩 Split into ${docSplits.length} chunks.`);

  const vectorStore = await Chroma.fromDocuments(
    docSplits,
    new OpenAIEmbeddings(),
    {
      collectionName: "a-test-collection",
      url: "http://localhost:8000",
    }
  );

  console.log("✅ Indexing completed. Data stored in Chroma DB.");
  return { success: true, count: docSplits.length };
}
