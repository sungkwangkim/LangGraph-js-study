import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import dotenv from "dotenv";

dotenv.config();
const model = new ChatGoogleGenerativeAI({
  model: "gemini-2.5-flash",
});

const res = await model.invoke([
  [
    "human",
    "한국에서 개쩌는 채용 플랫폼 회사는 어디일까요?",
    "Please answer in Korean."
  ],
]);

console.log(res)