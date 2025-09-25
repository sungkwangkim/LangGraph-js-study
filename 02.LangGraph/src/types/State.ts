import { Annotation } from "@langchain/langgraph";

export const GraphStateAnnotation = Annotation.Root({
  context: Annotation<string[]>({
    reducer: (state: string[], update: string[]) => state.concat(update),
    default: () => [],
  }),
  answer: Annotation<string[]>({
    reducer: (state: string[], update: string[]) => state.concat(update),
    default: () => [],
  }),
  question: Annotation<string>,
  sql_query: Annotation<string>,
  
  binary_score: Annotation<string>

  // #3
  // binary_score: Annotation<string[]>({
  //   reducer: (state: string[], update: string[]) => state.concat(update),
  //   default: () => [],
  // })

});