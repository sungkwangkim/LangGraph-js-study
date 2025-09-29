import { HumanMessage } from '@langchain/core/messages';

import { graph } from './agent/graph.ts';


const message = "잠실 남자들이 좋아하는 점심 메뉴 추천해줘."

const initialState = {
    messages: [new HumanMessage(message)],
  };

const result = await graph.invoke(initialState);

console.log(result)