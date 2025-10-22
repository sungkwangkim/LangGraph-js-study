import { createRetrieverTool } from "langchain/tools/retriever";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { retriever } from './retriever.ts'
import type { GraphState } from './state.ts'


// 잠실 맛집 블로그 게시물을 검색하는 도구를 생성합니다.
// 직장인들의 점심 메뉴 관련 정보를 검색합니다.
const tool = createRetrieverTool(
  retriever,
  {
    name: "retrieve_blog_posts",
    description:
      "송파구 잠실 및 잠실역 근처 점심 맛집 게시물을 검색하고 정보를 반환합니다.",
  },
);

// 사용 가능한 모든 도구를 배열로 내보냅니다.
export const tools = [tool];

// 도구들을 실행할 수 있는 노드를 생성합니다.
// 이 노드는 그래프 상태를 관리하며 도구 호출을 처리합니다.
export const toolNode = new ToolNode<typeof GraphState.State>(tools);