from typing import Annotated, Optional, List
from typing_extensions import TypedDict
import datetime
import uuid
from typing import Literal
import ast
import sys
import os
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import pprint
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import difflib
from copy import deepcopy
import json
import ast

#from src.agentic_system_1.database import save_state_to_aiven


state = {
    "process_id": 123456,
    "topic": "Company",
    "product": {},                 # dict -> tallennetaan JSONB:nä
    "transition": [1,2,3],
    "timestamps": [],    # datetime-objektit tai str
    "agent_scores": [0.7, 0.8, 0.9],
    "messages": [],
    "explanation": [{"key":"x","text":"why"}, "free text"],
    "product_ranking": {},  # dict -> tallennetaan JSONB:nä
    "finished": True,  # uusi sarake, oletuksena False
}
#save_state_to_aiven(state)            # käyttää DATABASE_URL:ia


try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from src.agentic_system_1.database import save_state_to_aiven as save_to_aiven
    print("Module imported successfully.")
    print("save_to_aiven type:", type(save_to_aiven))

except Exception as e:
    state["messages"].append(AIMessage(content=f"Import failed in s3: {e}"))
    state["next_node"] = 5
    print("\n--- s3 Node Deactivated (DATABASE.py module import error) ---")

print("Saving state to Aiven database...")

try:
    #pprint("State to be saved:\n\n", state)
    save_to_aiven(state)
    print("State saved successfully.")
    state["messages"].append(AIMessage(content="State saved successfully."))
except Exception as e:
    print(f"Error saving state: {e}")