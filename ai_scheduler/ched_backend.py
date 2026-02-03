import os
import datetime
import json
from typing import List, Optional

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

# Import Models
from models import MultiAgentState, CurrentState, ScheduleEvent

# Import Agents
from agents.orchestrator import orchestrator_agent
from agents.rag import rag_agent
from agents.scheduler import scheduler_agent
from agents.verifier import verifier_agent
from agents.chat import chat_agent
from agents.academic import academic_agent

# Import Logic & Database
from database import db_manager, checkpointer
from rag_engine import vector_manager
from utils import get_current_calendar_events, create_calendar_event



def response_synthesizer(state: MultiAgentState) -> dict:
    """
    Synthesizes final response from agent outputs.
    Also executes approved database operations.
    """
    orchestrator_output = state.get("orchestrator_output") or {}
    rag_output = state.get("rag_output") or {}
    scheduler_output = state.get("scheduler_output") or {}
    verifier_output = state.get("verifier_output") or {}
    chat_output = state.get("chat_output") or {}
    academic_output = state.get("academic_output") or {}
    current_state = state.get("current_state") or {}
    
    intent = orchestrator_output.get("intent", "chat")
    if hasattr(intent, "value"):
        intent = intent.value
    intent = str(intent)
    
    response_parts = []
    
    if intent == "academic" and academic_output:
        res = academic_output
        
        # Check if this is a simple response (from tool queries like "what courses am I enrolled in")
        if res.get("response"):
            response_parts.append(res.get("response"))
        else:
            # GPA Strategy format
            response_parts.append(f"🎓 **Academic Strategy Report**")
            response_parts.append(f"Current CGPA: **{res.get('current_cgpa', 'N/A')}**")
            response_parts.append(f"Target CGPA: **{res.get('target_cgpa', 'N/A')}**")
            
            if res.get('is_feasible'):
                response_parts.append(f"✅ Status: **Feasible**")
                if res.get('required_sgpa'):
                    response_parts.append(f"Required SGPA for this semester: **{res.get('required_sgpa'):.2f}**")
                
                combinations = res.get('suggested_grade_combinations', [])
                if combinations:
                    response_parts.append("\n📚 **Suggested Grade Paths:**")
                    for combo in combinations:
                        response_parts.append(f"- {combo}")
            else:
                response_parts.append(f"❌ Status: **{res.get('feasibility_message', 'Not Mathematically Possible')}**")
            
            response_parts.append(f"\n📝 **Rationale:** {res.get('optimization_rationale', '')}")
    
    if intent == "rag" and rag_output:
        response_parts.append(rag_output.get("synthesized_answer", ""))
        if rag_output.get("extracted_deadlines"):
            response_parts.append(f"\n📅 **Extracted Deadlines:** {json.dumps(rag_output['extracted_deadlines'], indent=2)}")
        if rag_output.get("extracted_tasks"):
            response_parts.append(f"\n✅ **Extracted Tasks:** {json.dumps(rag_output['extracted_tasks'], indent=2)}")
        if rag_output.get("extracted_timetable"):
            response_parts.append(f"\n🗓️ **Extracted Timetable:** {json.dumps(rag_output['extracted_timetable'], indent=2)}")
    
    elif intent == "scheduler" and scheduler_output:
        # The scheduler now executes tools directly. We just show the rationale/confirmations.
        response_parts.append(f"📋 **Scheduling Update:**\n{scheduler_output.get('scheduling_rationale', '')}")
        
        # We still show proposed events if any didn't get executed by tools for some reason (fallback)
        proposed = scheduler_output.get("proposed_events", [])
        if proposed:
            response_parts.append("\n🗓️ **Proposed (Not yet synced):**")
            for p in proposed:
                response_parts.append(f"- {p.get('title')} ({p.get('start_datetime')})")
    
    elif intent == "calendar":
        # Fetch from DB if current_state is empty
        events = current_state.get('existing_events', [])
        if not events:
            # Use user_id from state or default to 1
            user_id = state.get("user_id", 1)
            if isinstance(user_id, str):
                user_id = int(user_id) if user_id.isdigit() else 1
            events = db_manager.get_upcoming_events(user_id=user_id)
            
        if events:
            event_list = []
            for e in events[:10]:
                title = e.get('title') or e.get('summary', 'Untitled')
                start = e.get('start_datetime') or e.get('start', {}).get('dateTime', 'N/A')
                event_list.append(f"- {title} ({start})")
            response_parts.append("📆 **Upcoming Events:**\n" + "\n".join(event_list))
        else:
            response_parts.append("📆 No upcoming events found.")
    
    elif chat_output:
        response_parts.append(chat_output.get("response", ""))
        suggestions = chat_output.get("follow_up_suggestions", [])
        if suggestions:
            response_parts.append("\n💡 **Suggestions:** " + ", ".join(suggestions))
    
    final_response = "\n".join(response_parts) if response_parts else "I'm not sure how to help with that. Could you provide more details?"
    
    return {
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)]
    }

# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_after_orchestrator(state: MultiAgentState) -> str:
    orchestrator_output = state.get("orchestrator_output") or {}
    intent = orchestrator_output.get("intent", "chat")
    if hasattr(intent, "value"):
        intent = intent.value
    intent = str(intent)
    
    requires_context = orchestrator_output.get("requires_context", False)
    
    if intent == "scheduler" and requires_context:
        return "rag"
    
    intent_to_node = {
        "rag": "rag",
        "scheduler": "scheduler",
        "calendar": "synthesize",
        "academic": "academic",
        "chat": "chat"
    }
    return intent_to_node.get(intent, "chat")

def route_after_rag(state: MultiAgentState) -> str:
    orchestrator_output = state.get("orchestrator_output") or {}
    intent = orchestrator_output.get("intent", "")
    
    # Handle Enum objects
    if hasattr(intent, "value"):
        intent = intent.value
    intent = str(intent)
    
    if intent == "scheduler":
        return "scheduler"
    return "synthesize"

def route_after_scheduler(state: MultiAgentState) -> str:
    return "synthesize"

# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_multi_agent_graph():
    workflow = StateGraph(MultiAgentState)
    
    workflow.add_node("orchestrator", orchestrator_agent)
    workflow.add_node("rag", rag_agent)
    workflow.add_node("scheduler", scheduler_agent)
    workflow.add_node("academic", academic_agent)
    workflow.add_node("chat", chat_agent)
    workflow.add_node("synthesize", response_synthesizer)
    
    workflow.set_entry_point("orchestrator")
    
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "rag": "rag",
            "scheduler": "scheduler",
            "academic": "academic",
            "chat": "chat",
            "synthesize": "synthesize"
        }
    )
    
    workflow.add_conditional_edges(
        "rag",
        route_after_rag,
        {
            "scheduler": "scheduler",
            "synthesize": "synthesize"
        }
    )
    
    workflow.add_edge("scheduler", "synthesize")
    workflow.add_edge("academic", "synthesize")
    workflow.add_edge("chat", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile(checkpointer=checkpointer)

# Build the application
app = build_multi_agent_graph()

# ============================================================================
# INTERFACE FUNCTIONS
# ============================================================================

async def stream_query(
    user_query: str,
    pdf_paths: Optional[List[str]] = None,
    thread_id: str = "default",
    user_id: str = "default"
):
    """
    Asynchronous generator that streams response chunks from the multi-agent system.
    """
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    
    initial_state: MultiAgentState = {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "pdf_paths": pdf_paths or [],
        "user_id": user_id,
        "loop_count": 0,
        "orchestrator_output": None,
        "rag_output": None,
        "scheduler_output": None,
        "verifier_output": None,
        "chat_output": None,
        "academic_output": None,
        "current_state": None,
        "final_response": "",
        "error": None
    }
    
    final_response_content = ""
    last_node = None
    
    # Use astream_events to capture detailed execution info
    async for event in app.astream_events(initial_state, config=config, version="v2"):
        kind = event["event"]
        
        # When a node starts processing
        if kind == "on_chain_start":
            if event["name"] in ["orchestrator", "rag", "scheduler", "academic", "chat", "synthesize"]:
                last_node = event["name"]
                
        # Capture streaming tokens from the LLM if they are part of a targeted node
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield json.dumps({"type": "token", "content": str(content)})
        
        # When a node completes, we might want to send structured updates (like metadata)
        if kind == "on_chain_end":
            if event["name"] == "synthesize":
                data = event["data"]["output"]
                final_response_content = data.get("final_response", "")
    
    # Final metadata result
    yield json.dumps({
        "type": "final",
        "response": final_response_content,
        "status": "complete"
    })

def ingest_documents(pdf_paths: List[str], user_id: str = "default") -> bool:
    return vector_manager.ingest_documents(pdf_paths, user_id=user_id)

if __name__ == "__main__":
    print("Agentic Backend is ready. Run api.py to expose the endpoints.")
