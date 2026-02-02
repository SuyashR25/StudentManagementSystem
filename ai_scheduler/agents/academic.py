import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models import MultiAgentState, GPAStrategyOutput
from llm_config import chat_llm
from database import db_manager

def academic_agent(state: MultiAgentState) -> dict:
    """
    Academic Strategist Agent: Handles CGPA/GPA calculations, history management,
    course enrollment, and grade path optimization.
    """
    query = state.get("user_query", "")
    current_state = state.get("current_state") or {}
    
    # Fetch latest history from Database
    db_history = db_manager.get_full_academic_history(user_id=1)
    academic_history = db_history.model_dump()

    # Define tools and bind them to the LLM
    from utils import (
        get_current_date, list_available_courses, enroll_student_in_course, 
        unenroll_student_from_course, get_my_enrolled_courses, retrieve_from_docs
    )
    tools = [
        get_current_date, list_available_courses, enroll_student_in_course, 
        unenroll_student_from_course, get_my_enrolled_courses, retrieve_from_docs
    ]
    chat_llm_with_tools = chat_llm.bind_tools(tools)
    
    # SYSTEM PROMPT
    system_prompt_text = """You are an Academic Execution Agent. Your job is to MANAGE student enrollments and academic planning.

Today's Date Context: You can use the 'get_current_date' tool to resolve current vs past semesters.

CRITICAL RULES:
1. If the user says "enroll me", "add me", "register me", "put me in", or similar - YOU MUST CALL 'enroll_student_in_course'. Do NOT just provide instructions on how to do it manually.
2. Use 'get_my_enrolled_courses' for "what am I in?", "my schedule", "my subjects".
3. Use 'list_available_courses' for "what can I take?", "available courses", "catalog".
4. If you need to verify if a course exists before enrolling, you can call 'enroll_student_in_course' with the 'course_name' directly; the tool handles the lookup for you.

DO NOT tell the user to "Log into the student portal" or "Search for the course manually". YOU ARE THE PORTAL. Perform the action using your tools.

Current Academic History:
{history}

Current Semester Info:
{active_courses}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_text),
        ("human", "{query}")
    ])
    
    try:
        history_str = json.dumps(academic_history)
        active_courses = json.dumps(current_state.get("active_tasks", []))
        
        # 1. First Pass: Allow agent to call tools
        response = chat_llm_with_tools.invoke(prompt.format(
            history=history_str,
            active_courses=active_courses,
            query=query
        ))
        
        # 2. Process Tools (Loop for multi-step if needed)
        tool_map = {
            "get_current_date": get_current_date,
            "list_available_courses": list_available_courses,
            "enroll_student_in_course": enroll_student_in_course,
            "unenroll_student_from_course": unenroll_student_from_course,
            "get_my_enrolled_courses": get_my_enrolled_courses,
            "retrieve_from_docs": retrieve_from_docs
        }
        
        iteration = 0
        while hasattr(response, "tool_calls") and response.tool_calls and iteration < 3:
            iteration += 1
            tool_outputs = []
            
            # Use Tool Messages for LangChain consistency
            from langchain_core.messages import ToolMessage
            messages = [
                ("system", system_prompt_text.format(history=history_str, active_courses=active_courses)),
                ("human", query),
                response
            ]
            
            for tool_call in response.tool_calls:
                tool_func = tool_map.get(tool_call["name"])
                if tool_func:
                    tool_res = tool_func.invoke(tool_call["args"])
                    messages.append(ToolMessage(content=str(tool_res), tool_call_id=tool_call["id"]))
            
            # Get next response (might call more tools or final answer)
            response = chat_llm_with_tools.invoke(messages)

        content = response.content if isinstance(response.content, str) else str(response.content)
        
        return {"academic_output": {"response": content, "raw_content": content}}
        
    except Exception as e:
        return {"error": f"Academic execution error: {str(e)}"}
