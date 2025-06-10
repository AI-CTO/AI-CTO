from typing import Annotated
from typing_extensions import TypedDict
import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# --- 1. Määrittele tila ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- 2. Lataa avaimet ---
load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- 3. Työkalu ---
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    print("🔧 multiply_tool activated")
    return a * b

@tool 
def sumary(a: int, b: int) -> int:
    """Add two numbers."""
    print("🔧 sum_tool activated")
    return a + b

@tool
def division(a: int, b: int) -> int:
    """Divide two numbers."""
    print("🔧 div_tool activated")
    return a / b

# --- 4. Luo agentti työkalulla ---
agent_node = create_react_agent(llm, tools=[multiply, sumary, division])

# --- 5. Luo graafi ---
graph_builder = StateGraph(State)
graph_builder.add_node("agent", agent_node)
graph_builder.set_entry_point("agent")
graph = graph_builder.compile()

# --- 6. Käyttöliittymä ---
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

# --- 7. Käynnistä silmukka ---
if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            stream_graph_updates(user_input)
        except Exception as e:
            print(f"Error: {e}")
            break
