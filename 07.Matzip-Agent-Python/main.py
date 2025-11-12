from agent.graph import graph
from langchain_core.messages import HumanMessage, AIMessage

def get_agent_response(message: str):
    initial_state = {
        "messages": [HumanMessage(content=message)],
    }
    try:
        result = graph.invoke(initial_state)
        # The final response is in the last AIMessage of the 'messages' list
        final_response = next(
            (m.content for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content),
            "Sorry, I couldn't find an answer.",
        )
        return final_response
    except Exception as e:
        print(f"Error: {e}")
        return f"An error occurred: {e}"