from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from models import MultiAgentState, ChatOutput
from llm_config import chat_llm

def chat_agent(state: MultiAgentState) -> dict:
    """
    Chat Agent: Handles general conversation.
    Uses a fast LLM for natural responses.
    """
    query = state.get("user_query", "")
    messages = state.get("messages", [])
    
    parser = PydanticOutputParser(pydantic_object=ChatOutput)
    rag_output = state.get("rag_output") or {}
    
    # Extract context from RAG if available
    rag_context = ""
    if rag_output:
        rag_context = f"""
Information extracted from uploaded documents:
- Content: {rag_output.get('synthesized_answer', 'N/A')}
- Specific Deadlines: {json.dumps(rag_output.get('extracted_deadlines', []))}
- Timetable: {json.dumps(rag_output.get('extracted_timetable', []))}
"""
    
    # Build conversation context
    conv_history = ""
    for msg in messages[-5:]:  # Last 5 messages for context
        if isinstance(msg, HumanMessage):
            conv_history += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            conv_history += f"Assistant: {msg.content}\n"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful academic scheduling assistant. Be friendly, concise, and helpful.

You can help with:
- Scheduling study sessions and events
- Analyzing syllabus documents
- Managing calendar
- General academic questions

{rag_context}

Today's Date Context: You can use the 'get_current_date' tool to provide the exact date if the user asks.

Conversation History:
{history}

{format_instructions}"""),
        ("human", "{query}")
    ])
    
    try:
        # Initial invocation
        response = chat_llm.invoke(prompt.format(
            query=query,
            history=conv_history,
            rag_context=rag_context,
            format_instructions=parser.get_format_instructions()
        ))
        
        # Check for tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            from utils import get_current_date
            tool_outputs = []
            for tool_call in response.tool_calls:
                if tool_call["name"] == "get_current_date":
                    date_res = get_current_date.invoke(tool_call["args"])
                    tool_outputs.append(date_res)
            
            # Re-invoke with confirmed date context
            if tool_outputs:
                response = chat_llm.invoke(prompt.format(
                    query=f"{query} (Context: Today is {tool_outputs[0]})",
                    history=conv_history,
                    rag_context=rag_context,
                    format_instructions=parser.get_format_instructions()
                ))

        # Ensure response.content is a string
        content = response.content if isinstance(response.content, str) else str(response.content)
        parsed = parser.parse(content)
        return {"chat_output": parsed.model_dump()}
    except Exception as e:
        fallback = ChatOutput(
            response=f"I apologize, I encountered an issue. Could you rephrase that? Error: {str(e)}",
            sentiment="neutral"
        )
        return {"chat_output": fallback.model_dump(), "error": str(e)}
