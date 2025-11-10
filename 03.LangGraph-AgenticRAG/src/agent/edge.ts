import { END } from "@langchain/langgraph";
import { pull } from "langchain/hub";
import { z } from "zod";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { ChatOpenAI } from "@langchain/openai";
import { AIMessage } from "@langchain/core/messages";
import { tools } from './tool.ts'
import type { GraphState } from './state.ts'

/**
 * 에이전트가 더 많은 정보를 검색할지 아니면 프로세스를 종료할지 결정합니다.
 * 이 함수는 상태의 마지막 메시지에서 함수 호출이 있는지 확인합니다. 
 * 도구 호출이 있으면 정보 검색을 계속하고, 없으면 프로세스를 종료합니다.
 * @param {typeof GraphState.State} state - 모든 메시지를 포함한 에이전트의 현재 상태
 * @returns {string} - 검색 프로세스를 "계속"할지 "종료"할지 결정
 */
export function shouldRetrieve(state: typeof GraphState.State): string {
  const { messages } = state;
  console.log("---검색 여부 결정---");
  const lastMessage = messages[messages.length - 1];

  if ("tool_calls" in lastMessage && Array.isArray(lastMessage.tool_calls) && lastMessage.tool_calls.length) {
    console.log("---결정: 검색 진행---");
    return "retrieve";
  }

   // 도구 호출이 없으면 종료합니다.
  return END;
}

/**
 * 검색된 문서의 관련성에 따라 에이전트가 계속 진행할지 결정합니다.
 * 이 함수는 대화의 마지막 메시지가 FunctionMessage 타입인지 확인하여
 * 문서 검색이 수행되었는지 판단합니다. 그런 다음 미리 정의된 모델과 출력 파서를 사용하여
 * 사용자의 초기 질문에 대한 문서의 관련성을 평가합니다.
 * 문서가 관련이 있으면 대화를 완료하고, 그렇지 않으면 검색 프로세스를 계속합니다.
 * @param {typeof GraphState.State} state - 모든 메시지를 포함한 에이전트의 현재 상태
 * @returns {Promise<Partial<typeof GraphState.State>>} - 메시지 목록에 새 메시지가 추가된 업데이트된 상태
 */
export async function gradeDocuments(state: typeof GraphState.State): Promise<Partial<typeof GraphState.State>> {
  console.log("---관련성 평가---");

  const { messages } = state;
  const tool = {
    name: "give_relevance_score",
    description: "검색된 문서에 관련성 점수를 부여합니다.",
    schema: z.object({
      binaryScore: z.string().describe("관련성 점수 'yes' 또는 'no'"),
    })
  }

const prompt = ChatPromptTemplate.fromTemplate(
    `당신은 검색된 문서가 사용자 질문과 관련이 있는지 평가하는 채점자입니다.
  다음은 검색된 문서입니다:
  \n ------- \n
  {context}
  \n ------- \n
  다음은 사용자 질문입니다: {question}
  문서의 내용이 사용자 질문과 관련이 있으면 관련 있음으로 평가하세요.
  문서가 질문과 관련이 있는지 나타내는 'yes' 또는 'no'의 이진 점수를 부여하세요.
  Yes: 문서가 질문과 관련이 있습니다.
  No: 문서가 질문과 관련이 없습니다.`,
  );


  const model = new ChatOpenAI({
    model: "gpt-4o",
    temperature: 0,
  }).bindTools([tool], {
    tool_choice: tool.name,
  });

  const chain = prompt.pipe(model);

  const lastMessage = messages[messages.length - 1];

  const score = await chain.invoke({
    question: messages[0].content as string,
    context: lastMessage.content as string,
  });

  return {
    messages: [score]
  };
}

/**
 * 이전 LLM 도구 호출의 관련성을 확인합니다.
 *
 * @param {typeof GraphState.State} state - 모든 메시지를 포함한 에이전트의 현재 상태
 * @returns {string} - 문서의 관련성에 따라 "yes" 또는 "no" 반환
 */
export function checkRelevance(state: typeof GraphState.State): string {
  console.log("---관련성 확인---");

  const { messages } = state;
  const lastMessage = messages[messages.length - 1];
  if (!("tool_calls" in lastMessage)) {
    throw new Error("'checkRelevance' 노드는 가장 최근 메시지에 도구 호출이 포함되어야 합니다.")
  }
  const toolCalls = (lastMessage as AIMessage).tool_calls;
  if (!toolCalls || !toolCalls.length) {
    throw new Error("마지막 메시지가 함수 메시지가 아닙니다");
  }

  if (toolCalls[0].args.binaryScore === "yes") {
    console.log("---결정: 문서 관련 있음---");
    return "yes";
  }
  console.log("---결정: 문서 관련 없음---");
  return "no";
}

// Nodes

/**
 * 현재 상태를 기반으로 응답을 생성하기 위해 에이전트 모델을 호출합니다.
 * 이 함수는 에이전트 모델을 호출하여 현재 대화 상태에 대한 응답을 생성합니다.
 * 생성된 응답은 상태의 메시지에 추가됩니다.
 * @param {typeof GraphState.State} state - 모든 메시지를 포함한 에이전트의 현재 상태
 * @returns {Promise<Partial<typeof GraphState.State>>} - 메시지 목록에 새 메시지가 추가된 업데이트된 상태
 */
export async function agent(state: typeof GraphState.State): Promise<Partial<typeof GraphState.State>> {
  console.log("---에이전트 호출---");

  const { messages } = state;
  // `give_relevance_score` 도구 호출을 포함하는 AIMessage를 찾아서
  // 존재하면 제거합니다. 에이전트는 관련성 점수를 알 필요가 없기 때문입니다.
  const filteredMessages = messages.filter((message) => {
    if ("tool_calls" in message && Array.isArray(message.tool_calls) && message.tool_calls.length > 0) {
      return message.tool_calls[0].name !== "give_relevance_score";
    }
    return true;
  });

  // const model = new ChatGoogleGenerativeAI({
  //   model: "gemini-2.0-flash-lite",
  //   temperature: 0,
  //   streaming: true,
  // }).bindTools(tools);

  const model = new ChatOpenAI({
    model: "gpt-4o",
    temperature: 0,
    streaming: true,
  }).bindTools(tools);

  const response = await model.invoke(filteredMessages);
  return {
    messages: [response],
  };
}

/**
 * 더 나은 질문을 생성하기 위해 쿼리를 변환합니다.
 * @param {typeof GraphState.State} state - 모든 메시지를 포함한 에이전트의 현재 상태
 * @returns {Promise<Partial<typeof GraphState.State>>} - 메시지 목록에 새 메시지가 추가된 업데이트된 상태
 */
export async function rewrite(state: typeof GraphState.State): Promise<Partial<typeof GraphState.State>> {
  console.log("---쿼리 변환---");

  const { messages } = state;
  const question = messages[0].content as string;
  const prompt = ChatPromptTemplate.fromTemplate(
    `입력을 보고 기본적인 의미나 의도를 파악해보세요. \n
다음은 초기 질문입니다:
\n ------- \n
{question}
\n ------- \n
개선된 질문을 작성하세요:`,
  );

  // Grader
  // const model = new ChatGoogleGenerativeAI({
  //   model: "gemini-2.0-flash-lite",
  //   temperature: 0,
  //   streaming: true,
  // })

  const model = new ChatOpenAI({
    model: "gpt-4o",
    temperature: 0,
    streaming: true,
  });
  const response = await prompt.pipe(model).invoke({ question });
  return {
    messages: [response],
  };
}

/**
 * 답변을 생성합니다.
 * @param {typeof GraphState.State} state - 모든 메시지를 포함한 에이전트의 현재 상태
 * @returns {Promise<Partial<typeof GraphState.State>>} - 메시지 목록에 새 메시지가 추가된 업데이트된 상태
 */
export async function generate(state: typeof GraphState.State): Promise<Partial<typeof GraphState.State>> {
  console.log("---답변 생성---");

  const { messages } = state;
  const question = messages[0].content as string;
  // 가장 최근의 ToolMessage를 추출합니다
  const lastToolMessage = messages.slice().reverse().find((msg) => msg._getType() === "tool");
  if (!lastToolMessage) {
    throw new Error("대화 기록에서 도구 메시지를 찾을 수 없습니다");
  }

  const docs = lastToolMessage.content as string;

  const prompt = await pull<ChatPromptTemplate>("rlm/rag-prompt");

  // const llm = new ChatGoogleGenerativeAI({
  //   model: "gemini-2.0-flash-lite",
  //   temperature: 0,
  //   streaming: true,
  // })

  const llm = new ChatOpenAI({
    model: "gpt-4o",
    temperature: 0,
    streaming: true,
  });

  const ragChain = prompt.pipe(llm);

  const response = await ragChain.invoke({
    context: docs,
    question,
  });

  return {
    messages: [response],
  };
}