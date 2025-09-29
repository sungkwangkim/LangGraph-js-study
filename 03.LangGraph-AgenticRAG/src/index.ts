import { HumanMessage } from '@langchain/core/messages';

import { graph } from './agent/graph.ts';


const message = "점심에 파스타 잘하는 식당은?"

const initialState = {
    messages: [new HumanMessage(message)],
  };

const result = await graph.invoke(initialState);

console.log(result)