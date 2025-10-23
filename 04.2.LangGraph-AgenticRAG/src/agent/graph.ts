import { StateGraph, START, END } from "@langchain/langgraph";
import { agent, gradeDocuments, rewrite, generate, shouldRetrieve, checkRelevance} from './edge.ts'
import { toolNode } from './tool.ts'
import { GraphState } from './state.ts'

// 그래프 정의
const builder = new StateGraph(GraphState)
  // 순환할 노드들을 정의합니다.
  .addNode("agent", agent)
  .addNode("retrieve", toolNode)
  .addNode("gradeDocuments", gradeDocuments)
  .addNode("rewrite", rewrite)
  .addNode("generate", generate);



builder.addEdge(START, "agent");

// 검색 여부 결정
builder.addConditionalEdges(
  "agent",
  // 에이전트 결정 평가
  shouldRetrieve,
);

builder.addEdge("retrieve", "gradeDocuments");

// Edges taken after the `action` node is called.
builder.addConditionalEdges(
  "gradeDocuments",
  // Assess agent decision
  checkRelevance,
  {
    // Call tool node
    yes: "generate",
    no: "rewrite", // placeholder
  },
);

builder.addEdge("generate", END);
builder.addEdge("rewrite", "agent");

// Compile
export const graph = builder.compile();
