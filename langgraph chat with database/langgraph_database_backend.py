from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq  
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()

# =========================LLM Setup======================
llm = ChatGroq(
    model="llama-3.1-8b-instant",  # Fast, available model on Groq
    temperature=0.7,
)

# ==========================Graph Node Definition======================
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState) -> dict:
    try:
        response = llm.invoke(state["messages"])
        return {"messages": response}
    except Exception as e:
        print(f"Error in chat_node: {str(e)}")
        return {"messages": SystemMessage(content="Sorry, I hit an error. Please try again.")}

# ==========================Database Setup======================
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
# Set up memory checkpoint
checkpointer = SqliteSaver(conn=conn)
# ==========================Graph Definition======================
# Define the graph
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# Compile the graph with checkpointer
chatbot = graph.compile(checkpointer=checkpointer)

# ==========================Database Operations======================
# Function to load all messages from a thread
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)

# # ==========================testing====================
# CONFIG = {"configurable": {"thread_id": {"thread_id": "thread-1"}}}
# response = chatbot.invoke(
#     {"messages": [HumanMessage(content="what is my name")]},
#     config=CONFIG,
# )
# print(response)
