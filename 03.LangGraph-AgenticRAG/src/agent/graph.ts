import { StateGraph, START, END } from "@langchain/langgraph";
import { agent, gradeDocuments, rewrite, generate, shouldRetrieve, checkRelevance} from './edge.ts'
import { toolNode } from './tool.ts'
import { GraphState } from './state.ts'

// Define the graph
const builder = new StateGraph(GraphState)
  // Define the nodes which we'll cycle between.
  .addNode("agent", agent)
  .addNode("retrieve", toolNode)
  .addNode("gradeDocuments", gradeDocuments)
  .addNode("rewrite", rewrite)
  .addNode("generate", generate);



builder.addEdge(START, "agent");

// Decide whether to retrieve
builder.addConditionalEdges(
  "agent",
  // Assess agent decision
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
