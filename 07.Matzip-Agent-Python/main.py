from agent.graph import graph
from langchain_core.messages import HumanMessage

def main():
    message = "잠실에서 남자들이 점심먹기 좋은 곳은?"

    initial_state = {
        "messages": [HumanMessage(content=message)],
    }

    try:
        result = graph.invoke(initial_state)
        print(result)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
