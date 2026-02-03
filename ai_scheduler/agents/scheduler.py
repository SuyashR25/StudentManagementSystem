import json
import datetime
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models import MultiAgentState, SchedulerOutput, CurrentState
from llm_config import scheduler_llm
from database import db_manager

def scheduler_agent(state: MultiAgentState) -> dict:
    """
    Scheduler Agent: Proposes schedule updates.
    Uses tools to dynamically query the calendar context instead of full prompt injection.
    """
    query = state.get("user_query", "")
    rag_output = state.get("rag_output", {})
    current_state = state.get("current_state", {})
    
    parser = PydanticOutputParser(pydantic_object=SchedulerOutput)
    
    # Extract context from RAG if available
    rag_context = ""
    if rag_output:
        rag_context = f"""
Information extracted from user documents:
- Deadlines: {json.dumps(rag_output.get('extracted_deadlines', []))}
- Timetable: {json.dumps(rag_output.get('extracted_timetable', []))}
"""
    
    today_now = datetime.datetime.now()
    today_val = today_now.strftime("%Y-%m-%d")
    day_name = today_now.strftime("%A")

    # Generate next 14 days mapping for absolute accuracy
    date_mapping = []
    for i in range(14):
        future_date = today_now + datetime.timedelta(days=i)
        date_mapping.append(f"- {future_date.strftime('%A')}: {future_date.strftime('%Y-%m-%d')}")
    date_context = "\n".join(date_mapping)

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a high-level Scheduling & Execution Agent. You manage the user's calendar by combining direct instructions with information retrieved from academic documents.

Your capabilities:
1. **Search/List**: Use 'search_calendar' or 'list_calendar_events' to see the current state of the calendar.
2. **Calendar CRUD**: Use 'add_event', 'update_calendar_event', 'delete_calendar_event', 'delete_events_on_date', or 'clear_full_calendar' to modify the schedule.
3. **Contextual awareness**: Use 'get_current_date' to resolve relative time (e.g., "next Monday").

If a user wants to schedule classes from a timetable (provided in RAG context):
- ONLY add events if the user's query is about scheduling or adding classes.
- If the user's query is to CLEAR, DELETE, or SEARCH, do that FIRST and IGNORE the RAG timetable unless specifically asked to add it.
- YOU MUST CALL 'add_event' SEPARATELY FOR EVERY SINGLE CLASS SLOT FOUND IN THE RAG CONTEXT (if adding).
- USE THE DATE MAPPING BELOW to resolve day names (e.g., "Monday") to the correct date.
- Pick the FIRST occurrence of that day name starting from today ({today_val}) or the next week as appropriate.
- DO NOT schedule everything on the same day. Use the date that matches the day name.
- DO NOT summarize classes in text until you have made the tool calls.

**CRITICAL CLEARING INSTRUCTION:**
If the user asks to "clear", "wipe", "delete everything", or "reset" the calendar, you MUST immediately call `clear_full_calendar` as your FIRST and ONLY tool call. Do NOT call list_calendar_events or retrieve_from_docs first. Just call clear_full_calendar directly.

Upcoming Date Mapping (Next 14 Days):
{date_context}

Today's Date: {today_val} ({day_name})

{{rag_context}}

{{format_instructions}}"""),
        ("human", "Scheduling Request: {{query}}")
    ])
    try:
        # Initial invocation
        response = scheduler_llm.invoke(prompt.format(
            query=query,
            rag_context=rag_context,
            format_instructions=parser.get_format_instructions()
        ))
        # --- TOOL CALL LOOP (Handles CRUD tools) ---
        iterations = 0
        executed_actions = set() # Track unique actions to prevent loops (except read-only)
        
        while hasattr(response, "tool_calls") and response.tool_calls and iterations < 6:
            iterations += 1
            from utils import (
                get_current_date, list_calendar_events, search_calendar, add_event, 
                delete_calendar_event, delete_events_on_date, update_calendar_event, 
                clear_full_calendar, list_available_courses, enroll_student_in_course, 
                unenroll_student_from_course, get_my_enrolled_courses, retrieve_from_docs
            )
            tool_map = {
                "get_current_date": get_current_date,
                "list_calendar_events": list_calendar_events,
                "search_calendar": search_calendar,
                "add_event": add_event,
                "delete_calendar_event": delete_calendar_event,
                "delete_events_on_date": delete_events_on_date,
                "update_calendar_event": update_calendar_event,
                "clear_full_calendar": clear_full_calendar,
                "list_available_courses": list_available_courses,
                "enroll_student_in_course": enroll_student_in_course,
                "unenroll_student_from_course": unenroll_student_from_course,
                "get_my_enrolled_courses": get_my_enrolled_courses,
                "retrieve_from_docs": retrieve_from_docs
            }
            
            tool_context = []
            new_actions_performed = False
            
            for tool_call in response.tool_calls:
                t_name = tool_call["name"]
                t_args_str = json.dumps(tool_call["args"], sort_keys=True) 
                action_signature = f"{t_name}:{t_args_str}" # Use for tracking executed actions
                
                print(f"DEBUG: Executing tool '{t_name}' with args {t_args_str}")
                
                # Check for duplicates, but allow read-only tools to re-run
                if action_signature in executed_actions:
                    if t_name not in ["list_calendar_events", "search_calendar", "retrieve_from_docs"]: # Updated condition from instruction
                        print(f"DEBUG: Skipping duplicate tool call: {t_name}")
                        tool_context.append(f"Result for already executed action: {t_name} was successful.")
                        continue
                    
                if t_name in tool_map:
                    try:
                        # Inject user_id into tool arguments
                        t_args = tool_call["args"]
                        user_id_val = state.get("user_id", "1")
                        if "user_id" not in t_args:
                            try:
                                t_args["user_id"] = int(user_id_val) if str(user_id_val).isdigit() else 1
                            except:
                                t_args["user_id"] = 1

                        res = tool_map[t_name].invoke(t_args)
                        print(f"DEBUG: Tool '{t_name}' returned: {str(res)[:100]}")
                        tool_context.append(f"Tool Result ({t_name}): {res}")
                        executed_actions.add(action_signature)
                        new_actions_performed = True
                    except Exception as e:
                        print(f"DEBUG: Tool '{t_name}' error: {e}")
                        tool_context.append(f"Tool Error ({t_name}): {str(e)}")
                else:
                    print(f"DEBUG: Tool '{t_name}' not in tool_map!")
                    tool_context.append(f"Action: {t_name} -> Error: Tool not found")
            
            # Smart Breaking Condition
            if not new_actions_performed:
                # If we didn't do anything new (all dupes), break to prevent infinite loop
                if iterations > 1: 
                    break
            
            # Re-invoke with context
            if tool_context:
                query_with_tools = f"{query}\n\nHistory of Executed Actions:\n" + "\n".join(tool_context)
                response = scheduler_llm.invoke(prompt.format(
                    query=query_with_tools + "\n\nCRITICAL: DO NOT call add_event for events that are already 'Successfully added' or 'Skipped' in the History above. Provide a final summary and return the JSON 'scheduling_rationale'.",
                    rag_context=rag_context,
                    format_instructions=parser.get_format_instructions()
                ))
            else:
                break
 # executed 0 tools? break.

        # Validation and Parsing Logic
        content = response.content if isinstance(response.content, str) else str(response.content)
        
        parsed = None
        # 1. Direct Parse
        try:
            parsed = parser.parse(content)
        except:
            pass
            
        # 2. Extract JSON
        if parsed is None and "```json" in content:
            match = re.search(r"```json(.*?)```", content, re.DOTALL)
            if match:
                try:
                    parsed = parser.parse(match.group(1).strip())
                except:
                    pass
        
        # 3. Fallback to Text
        if parsed is None:
            # Clean generic thinking tags
            clean_text = content.replace("<tool_code>", "").replace("</tool_code>", "")
            parsed = SchedulerOutput(
                scheduling_rationale=clean_text,
                proposed_events=[]
            )

        return {
            "scheduler_output": parsed.model_dump(),
            "current_state": current_state
        }
    except Exception as e:
        import traceback
        print(f"ERROR in scheduler_agent: {str(e)}")
        traceback.print_exc()
        fallback = SchedulerOutput(
            scheduling_rationale=f"Error in scheduling: {str(e)}"
        )
        return {"scheduler_output": fallback.model_dump(), "error": str(e)}
