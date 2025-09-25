import { StateGraph, START, END } from "@langchain/langgraph";
import { GraphStateAnnotation } from "./types/State.ts";


const retrieve = (state) => {
  console.log("-> retrieve: 문서 검색");
  const documents = "검색된 문서";
  return { 
    context: [documents]
  };
};

const llmGptExecute = (state) => {
  console.log("-> llmGptExecute: GPT LLM 실행");
  const answer = "GPT 생성된 답변";
  return { 
    answer: [answer]
  };
};

const llmClaudeExecute = (state) => {
  console.log("-> llmClaudeExecute: Claude LLM 실행");
  const answer = "Claude 의 생성된 답변";
  return { 
    answer: [answer]
  };
};

const relevanceCheck = (state) => {
  console.log("-> relevanceCheck: 관련성 확인");
  const binaryScore = "yes"; // "yes" 또는 "no"로 가정
  return { 
    binary_score: binaryScore
  };
};

const sumUp = (state) => {
  console.log("-> sumUp: 결과 종합");
  const answer = "종합된 답변";
  return { 
    answer: [answer]
  };
};

const searchOnWeb = (state) => {
  console.log("-> searchOnWeb: 웹 검색");
  let documents = state.context || "";
  const searchedDocuments = "웹에서 검색된 문서";
  documents += searchedDocuments;
  return { 
    context: [documents]
  };
};

const decision = (state) => {
  console.log("-> decision: 의사결정");
  
  if (state.binary_score === "yes") {
    return "종료";
  } else {
    return "재검색";
  }

  // #3
  // if (state.binary_score.include("yes")) {
  //   return "종료";
  // } else {
  //   return "재검색";
  // }
};


const builder = new StateGraph(GraphStateAnnotation);

// 노드를 추가 __START__
builder.addNode("retrieve", retrieve);
builder.addNode("GPT 요청", llmGptExecute);
builder.addNode("GPT_relevance_check", relevanceCheck);


// builder.addNode("Claude 요청", llmClaudeExecute); // #3
// builder.addNode("Claude_relevance_check", relevanceCheck); // #3

builder.addNode("결과 종합", sumUp);
// 노드를 추가 __END__


// EDGE를 추가 __START__
builder.addEdge(START, "retrieve");
builder.addEdge("retrieve", "GPT 요청");
// builder.addEdge("retrieve", "Claude 요청"); // #3

builder.addEdge("GPT 요청", "GPT_relevance_check");
builder.addEdge("GPT_relevance_check", "결과 종합");

// builder.addEdge("Claude 요청", "Claude_relevance_check"); // #3
// builder.addEdge("Claude_relevance_check", "결과 종합"); // #3

builder.addEdge("결과 종합", END);


// #2
// builder.addConditionalEdges("결과 종합", decision, {
//   "재검색": "retrieve",
//   "종료": END
// })

// EDGE를 추가 __END__


const graph = builder.compile();

const result = await graph.invoke({ question: 'hello' });
console.log("Graph invoke 결과:", result);
