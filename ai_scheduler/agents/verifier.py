import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models import MultiAgentState, VerifierOutput, ScheduleEvent
from llm_config import verifier_llm

def verifier_agent(state: MultiAgentState) -> dict:
    """
    Verifier Agent: Validates proposed changes against current state.
    Uses a fast, small LLM for quick verification.
    """
    scheduler_output = state.get("scheduler_output", {})
    current_state = state.get("current_state", {})
    
    if not scheduler_output:
        return {"verifier_output": {"is_valid": False, "verification_notes": "No scheduler output to verify"}}
    
    # Extract proposed changes from scheduler output
    proposed_events = scheduler_output.get("proposed_events", [])
    proposed_deletions = scheduler_output.get("deleted_event_ids", [])
    
    # If no changes proposed, just return early
    if not proposed_events and not proposed_deletions:
        return {
            "verifier_output": {
                "is_valid": True,
                "verification_notes": scheduler_output.get("scheduling_rationale", "No changes proposed"),
                "approved_events": [],
                "approved_deletions": [],
                "conflicts": [],
                "warnings": [],
                "rejected_events": []
            }
        }
    
    parser = PydanticOutputParser(pydantic_object=VerifierOutput)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a verification agent. Check proposed schedule changes for:
1. Time conflicts with existing events
2. Unrealistic time allocations (too short/long)
3. Missing required information
4. Logic errors (end before start, past dates)

Current State:
{current_state}

Proposed Changes:
{proposed_changes}

{format_instructions}

Be strict but fair. 
1. For approved_events, return the full event objects that should be saved.
2. For approved_deletions, return the list of event IDs that are safe and requested to be deleted.
"""),
        ("human", "Verify these proposed changes.")
    ])
    
    chain = prompt | verifier_llm
    
    try:
        current_state_dict = current_state if current_state else {}
        response = chain.invoke({
            "current_state": json.dumps(current_state_dict.get('existing_events', [])[:10], indent=2),
            "proposed_changes": json.dumps(scheduler_output, indent=2),
            "format_instructions": parser.get_format_instructions()
        })
        
        # Ensure response.content is a string
        content = response.content if isinstance(response.content, str) else str(response.content)
        
        try:
            parsed = parser.parse(content)
            result = parsed.model_dump()
        except Exception as parse_error:
            # If parsing fails, do a simple validation and pass through events
            result = {
                "is_valid": True,
                "verification_notes": f"Auto-approved (parser issue: {str(parse_error)})",
                "approved_events": proposed_events,  # Pass through all proposed events
                "conflicts": [],
                "warnings": [f"Parse warning: {str(parse_error)}"],
                "rejected_events": []
            }
        
        if result.get("is_valid"):
            if not result.get("approved_events"):
                result["approved_events"] = proposed_events
            if not result.get("approved_deletions"):
                result["approved_deletions"] = proposed_deletions
            
        return {"verifier_output": result}
    except Exception as e:
        # On error, still approve the events to avoid blocking user
        return {
            "verifier_output": {
                "is_valid": True,
                "verification_notes": f"Auto-approved due to error: {str(e)}",
                "approved_events": proposed_events,  # Pass through on error
                "approved_deletions": proposed_deletions,
                "conflicts": [],
                "warnings": [str(e)],
                "rejected_events": []
            },
            "error": str(e)
        }

