from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage
import datetime
from models import MultiAgentState, OrchestratorOutput, AgentType
from llm_config import orchestrator_llm

def orchestrator_agent(state: MultiAgentState) -> dict:
    """
    Orchestrator Agent: Routes queries to appropriate agents.
    Uses a fast, small LLM for low latency.
    """
    user_query = state.get("user_query", "")
    if not user_query and state.get("messages"):
        # Get last human message
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break
    
    # Ensure user_query is a string
    if isinstance(user_query, list):
        user_query = " ".join(str(item) for item in user_query)
    else:
        user_query = str(user_query)
    
    parser = PydanticOutputParser(pydantic_object=OrchestratorOutput)
    
    # Check if PDFs are provided - if so, prioritize RAG routing
    pdf_paths = state.get("pdf_paths", [])
    pdf_hint = ""
    if pdf_paths:
        pdf_hint = f"\n\nIMPORTANT: The user has uploaded documents ({len(pdf_paths)} files). If their query relates to extracting information from a document, route to 'rag'."
    
    today_now = datetime.datetime.now()
    today_val = today_now.strftime("%Y-%m-%d")
    day_name = today_now.strftime("%A")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a fast routing orchestrator. Analyze the user query and determine which agent should handle it.

Today's Date: {today} ({day_name})

Agent Types:
- rag: Questions about documents, PDFs, syllabi, extracting information/tasks/timetables/events from files. Use this if documents are uploaded.
- scheduler: Creating, modifying, or DELETING schedule/calendar events based on user requests or extracted document data. Use this for ANY changes to the schedule.
- calendar: Viewing existing calendar events checking availability, listing what's planned (Read-only operations)
- academic: GPA calculation, academic history, CGPA targets, grade path optimization, course enrollment management
- chat: General conversation, greetings, help requests, unclear queries

Rules for Routing:
1. ANY request to DELETE, CLEAR, REMOVE, or WIPE events MUST be routed to 'scheduler'. Never route deletions to 'calendar'.
2. If 'pdf_paths' is NOT empty and the query is about scheduling, tasks, or information, YOU MUST route to 'rag' first (or set 'requires_context' to true).
3. If the user mentions "this file", "the document", "my syllabus", "timetable", or "from the PDF", route to 'rag'.
4. If the user wants to PLAN/SCHEDULE based on document information, route to 'scheduler' and set 'requires_context' to true (this triggers a RAG lookup first).
5. Use 'calendar' ONLY for reading existing events already in the database.
{pdf_hint}

{format_instructions}

Be decisive and quick. Extract key entities (dates, tasks, subjects) from the query. Ensure 'requires_context' is False for simple deletions.
"""),
        ("human", "User Query: {query}")
    ])
    
    try:
        from llm_config import chat_llm # Use chat_llm for orchestrator to avoid tool conflicts
        response = chat_llm.invoke(prompt.format(
            query=user_query,
            today=today_val,
            day_name=day_name,
            pdf_hint=pdf_hint,
            format_instructions=parser.get_format_instructions()
        ))
        
        # Parse the structured output
        content = response.content if isinstance(response.content, str) else str(response.content)
        clean_content = content.strip()
        
        # Robust JSON extraction
        if "```json" in clean_content:
            import re
            match = re.search(r"```json(.*?)```", clean_content, re.DOTALL)
            if match:
                clean_content = match.group(1).strip()
        elif "{" in clean_content and "}" in clean_content:
            start_index = clean_content.find("{")
            end_index = clean_content.rfind("}") + 1
            clean_content = clean_content[start_index:end_index]

        try:
            parsed = parser.parse(clean_content)
            print(f"DEBUG: Orchestrator detected intent: {parsed.intent}")
        except Exception as pe:
            # Prioritize scheduler for modifications
            requires_context = False
            if any(k in lower_content for k in ["clear", "delete", "remove", "update", "schedule", "add"]):
                detected_intent = AgentType.SCHEDULER
                # Only require context if specifically asking about documents or adding from them
                if "from" in lower_content or "pdf" in lower_content or "document" in lower_content:
                    requires_context = True
            elif any(k in lower_content for k in ["rag", "pdf", "document", "timetable", "syllabus"]):
                detected_intent = AgentType.RAG
                requires_context = True
            elif "calendar" in lower_content or "events" in lower_content:
                detected_intent = AgentType.CALENDAR
            
            print(f"DEBUG: Orchestrator FALLBACK intent: {detected_intent}, requires_context: {requires_context}")
            parsed = OrchestratorOutput(
                intent=detected_intent,
                confidence=0.4,
                query_summary=user_query,
                requires_context=requires_context,
                reasoning=f"Naive fallback due to parsing error: {str(pe)}"
            )

        return {
            "orchestrator_output": parsed.model_dump(),
            "user_query": user_query
        }
    except Exception as e:
        # Final fallback
        fallback = OrchestratorOutput(
            intent=AgentType.CHAT,
            confidence=0.1,
            query_summary=user_query,
            reasoning=f"Critical fallback: {str(e)}"
        )
        return {
            "orchestrator_output": fallback.model_dump(),
            "user_query": user_query,
            "error": str(e)
        }
