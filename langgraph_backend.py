from typing import TypedDict,Annotated,Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel,Field
from langchain_core.messages import SystemMessage, HumanMessage,BaseMessage
import operator
from langgraph.checkpoint.memory import MemorySaver
load_dotenv()

# 1. Initialize the model
model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7,
    max_tokens=500,
)

llm=model

from langgraph.graph.message import add_messages

class ChatState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages] # all type message in inherit Basemessage

def chat_node(state: ChatState):

    # take user query from state
    messages = state['messages']

    # send to llm
    response = llm.invoke(messages)

    # response store state
    return {'messages': [response]}

checkpointer=MemorySaver()
graph = StateGraph(ChatState)

# add nodes
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)
thread=1

