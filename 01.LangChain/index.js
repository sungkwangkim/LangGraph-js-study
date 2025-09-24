import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import dotenv from "dotenv";

dotenv.config();
const model = new ChatGoogleGenerativeAI({
  model: "gemini-2.5-flash",
});

const res = await model.invoke([
  [
    "human",
    "한국에서 개쩌는 회사 이름은 무엇일까요?",
    "Please answer in Korean."
  ],
]);

console.log(res)