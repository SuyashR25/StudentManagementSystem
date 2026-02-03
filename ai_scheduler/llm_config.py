from dotenv import load_dotenv
import os

# Load from absolute path to be safe
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(PARENT_DIR, ".env.local"))
load_dotenv(os.path.join(PARENT_DIR, ".env"))
load_dotenv() # Final fallback to local .env

from langchain_openai import ChatOpenAI
from utils import (
    get_current_date, list_calendar_events, search_calendar, add_event, 
    delete_calendar_event, delete_events_on_date, update_calendar_event, 
    clear_full_calendar, retrieve_from_docs,
    list_available_courses, enroll_student_in_course, 
    unenroll_student_from_course, get_my_enrolled_courses
)


llm = ChatOpenAI(
    model = "openai/gpt-oss-120b",
    base_url = "https://openrouter.ai/api/v1",
    api_key = os.getenv("OPENROUTER_API_KEY"),
    max_tokens = 512,
    temperature = 0.1
)
# Tools list
tools = [
    get_current_date, list_calendar_events, search_calendar, add_event, 
    delete_calendar_event, delete_events_on_date, update_calendar_event, 
    clear_full_calendar, retrieve_from_docs,
    list_available_courses, enroll_student_in_course, 
    unenroll_student_from_course, get_my_enrolled_courses
]

orchestrator_tools = [get_current_date]
orchestrator_llm = llm.bind_tools(orchestrator_tools)
verifier_llm = llm
chat_llm = llm

# Capable LLM for RAG and Scheduler
rag_llm = llm
scheduler_llm = llm.bind_tools(tools)

# Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')