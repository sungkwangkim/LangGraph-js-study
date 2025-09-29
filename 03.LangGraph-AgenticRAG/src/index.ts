import { HumanMessage } from '@langchain/core/messages';

import { graph } from './agent/graph.ts';


const message = "프롬프트 엔지니어링에 Zero-Shot란 무엇인가?"

const initialState = {
    messages: [new HumanMessage(message)],
  };

const result = await graph.invoke(initialState);

console.log(result)