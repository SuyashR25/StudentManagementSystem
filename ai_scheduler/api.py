import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Security, File, UploadFile
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the core logic from ched_backend
from ched_backend import stream_query
from database import db_manager
from models import TodoItem


load_dotenv()

# ============================================================================
# CONSTANTS & SETUP
# ============================================================================

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================================
# API KEY AUTHENTICATION
# ============================================================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    """Validates the API key from the header."""
    expected_key = os.getenv("API_KEY", "default-secret-key")
    if api_key == expected_key:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="Invalid or missing API Key"
    )

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(title="Ched Agentic Backend API")

# ============================================================================
# TODO ENDPOINTS
# ============================================================================

class TodoRequest(BaseModel):
    user_id: str = "1"
    text: str
    due_date: Optional[str] = None
    priority: Optional[str] = "Medium"
    tag: Optional[str] = "General"

class TodoUpdate(BaseModel):
    completed: Optional[bool] = None
    text: Optional[str] = None

@app.get("/todos")
async def get_todos(user_id: str = "1", api_key: str = Depends(get_api_key)):
    """Fetch all todos for a user."""
    uid = int(user_id) if user_id.isdigit() else 1
    return {"todos": db_manager.get_todos(uid)}

@app.post("/todos")
async def add_todo(request: TodoRequest, api_key: str = Depends(get_api_key)):
    """Add a new todo."""
    uid = int(request.user_id) if request.user_id.isdigit() else 1
    todo_id = db_manager.add_todo(
        user_id=uid,
        text=request.text,
        due_date=request.due_date,
        priority=request.priority,
        tag=request.tag
    )
    return {"status": "success", "todo_id": todo_id}

@app.patch("/todos/{todo_id}")
async def update_todo(todo_id: int, request: TodoUpdate, api_key: str = Depends(get_api_key)):
    """Update a todo."""
    success = db_manager.update_todo(todo_id, completed=request.completed, text=request.text)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"status": "success"}

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, api_key: str = Depends(get_api_key)):
    """Delete a todo."""
    success = db_manager.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"status": "success"}

@app.delete("/todos")
async def clear_todos(user_id: str = "1", api_key: str = Depends(get_api_key)):
    """Clear all todos for a user."""
    uid = int(user_id) if user_id.isdigit() else 1
    db_manager.clear_all_todos(uid)
    return {"status": "success"}

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key", "Content-Type"],
    expose_headers=["*"],
)


# Supported file extensions for document upload
SUPPORTED_EXTENSIONS = {".pdf", ".ppt", ".pptx"}

class QueryRequest(BaseModel):
    query: str
    file_paths: Optional[List[str]] = None  # Supports PDF, PPT, PPTX
    pdf_paths: Optional[List[str]] = None   # Legacy support
    thread_id: str = "default"
    user_id: str = "1"  # String for flexibility, defaults to "1"

from fastapi.responses import StreamingResponse
import json

@app.post("/query")
async def api_process_query(request: QueryRequest, api_key: str = Depends(get_api_key)):
    """Exposed endpoint to process queries using the multi-agent system with streaming."""
    try:
        from ched_backend import stream_query
        from database import db_manager
        
        uid = int(request.user_id) if request.user_id.isdigit() else 1
        
        # Save user message immediately
        db_manager.save_message(
            user_id=uid,
            thread_id=request.thread_id,
            role="user",
            message=request.query,
            intent=None
        )
        
        all_paths = (request.file_paths or []) + (request.pdf_paths or [])

        async def event_generator():
            final_response = ""
            async for chunk_str in stream_query(
                request.query, 
                all_paths if all_paths else None, 
                request.thread_id,
                uid
            ):
                chunk = json.loads(chunk_str)
                if chunk["type"] == "final":
                    final_response = chunk.get("response", "")
                    # We save the final response to DB here at the end of the stream
                    db_manager.save_message(
                        user_id=uid,
                        thread_id=request.thread_id,
                        role="assistant",
                        message=final_response,
                        intent="chat" # Defaulting for now as orchestrator intent is nested
                    )
                # Yield to the client
                yield f"data: {chunk_str}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    """
    Endpoint to upload documents (PDF, PPT, PPTX) for RAG processing.
    Returns the local path of the saved file.
    """
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "filename": file.filename,
            "path": file_path,
            "file_type": file_ext.replace('.', ''),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@app.get("/supported-formats")
async def get_supported_formats():
    """Returns list of supported file formats for document upload."""
    return {
        "supported_extensions": list(SUPPORTED_EXTENSIONS),
        "description": "PDF documents, PowerPoint presentations (PPT/PPTX)"
    }

@app.get("/courses")
async def get_courses(api_key: str = Depends(get_api_key)):
    """Returns the list of available courses from the JSON data file."""
    try:
        courses = db_manager.get_all_courses()
        return {"courses": courses, "count": len(courses)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load courses: {str(e)}")

@app.get("/enrolled-courses")
async def get_enrolled_courses(api_key: str = Depends(get_api_key)):
    """Fetch all courses the user is currently enrolled in."""
    try:
        courses = db_manager.get_enrolled_courses(user_id=1)
        return {"courses": courses, "count": len(courses)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EnrollRequest(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    credits: int = 3

@app.post("/enroll")
async def enroll_course(request: EnrollRequest, api_key: str = Depends(get_api_key)):
    """Enroll the user in a new course."""
    success = db_manager.enroll_in_course(
        user_id=1, 
        course_id=request.course_id,
        course_name=request.course_name, 
        course_code=request.course_code, 
        credits=request.credits
    )
    if success:
        return {"status": "success", "message": f"Enrolled in {request.course_name}"}
    return {"status": "error", "message": f"Already enrolled in {request.course_name} or course not found"}

@app.delete("/unenroll/{course_id}")
async def unenroll_course(course_id: int, api_key: str = Depends(get_api_key)):
    """Drop a course enrollment."""
    success = db_manager.unenroll_from_course(user_id=1, course_id=course_id)
    if success:
        return {"status": "success", "message": f"Dropped course {course_id}"}
    raise HTTPException(status_code=404, detail="Course enrollment not found")

# ============================================================================
# CALENDAR ENDPOINTS (Frontend Sync)
# ============================================================================

from database import db_manager
from models import ScheduleEvent

class EventCreateRequest(BaseModel):
    title: str
    start_datetime: str  # ISO format: "2026-01-25T15:00:00"
    end_datetime: str
    priority: str = "medium"  # low, medium, high
    category: str = "general"  # academic, personal, work, general
    description: str = ""
    source: str = "manual"
    user_id: Optional[str] = "1"

class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

@app.get("/events")
async def get_events(
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: str = Depends(get_api_key)
):
    """
    Get calendar events. 
    Optional: Filter by date range (start_date, end_date) in ISO format.
    """
    if start_date and end_date:
        events = db_manager.get_events_by_range(user_id=1, start_date=start_date, end_date=end_date)
    else:
        events = db_manager.get_upcoming_events(user_id=1, limit=limit)
        
    return {
        "events": events,
        "count": len(events)
    }


@app.get("/events/search")
async def search_events(
    query: Optional[str] = None,
    date: Optional[str] = None,  # Format: YYYY-MM-DD
    api_key: str = Depends(get_api_key)
):
    """
    Search events by keyword or date.
    - query: Search in title and description
    - date: Filter by specific date (YYYY-MM-DD)
    """
    events = db_manager.search_events(user_id=1, query=query, date=date)
    return {
        "events": events,
        "count": len(events),
        "filters": {"query": query, "date": date}
    }

@app.post("/events")
async def create_event(
    event: EventCreateRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Manually create a calendar event.
    Events created via chat are auto-saved, but this allows direct creation.
    """
    try:
        # Normalize priority to match model expectations (capitalized)
        priority_map = {"low": "Low", "medium": "Medium", "high": "High"}
        normalized_priority = priority_map.get(event.priority.lower(), "Medium")
        
        # Normalize category (capitalize first letter)
        normalized_category = event.category.capitalize() if event.category else "General"
        
        schedule_event = ScheduleEvent(
            title=event.title,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            priority=normalized_priority,
            category=normalized_category,
            description=event.description,
            source=event.source

        )
        db_manager.add_schedule_event(schedule_event, user_id=1)
        return {
            "status": "success",
            "message": f"Event '{event.title}' created successfully",
            "event": event.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/events/{event_id}")
async def update_event(
    event_id: int,
    updates: EventUpdateRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Update an existing calendar event.
    Only provided fields will be updated.
    """
    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No update fields provided")
    
    success = db_manager.update_event(event_id=event_id, user_id=1, updates=update_dict)
    
    if success:
        return {
            "status": "success",
            "message": f"Event {event_id} updated",
            "updated_fields": list(update_dict.keys())
        }
    else:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

@app.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    api_key: str = Depends(get_api_key)
):
    """
    Delete a calendar event by ID.
    """
    success = db_manager.delete_event(event_id=event_id, user_id=1)
    
    if success:
        return {
            "status": "success",
            "message": f"Event {event_id} deleted"
        }
    else:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

@app.delete("/events/date/{date_str}")
async def delete_events_by_date(
    date_str: str,
    api_key: str = Depends(get_api_key)
):
    """
    Delete all events on a specific date (YYYY-MM-DD).
    """
    count = db_manager.delete_events_by_date(date_str, user_id=1)
    return {
        "status": "success",
        "message": f"Deleted {count} events on {date_str}",
        "count": count
    }

@app.get("/events/today")
async def get_today_events(api_key: str = Depends(get_api_key)):
    """Get all events for today."""
    from datetime import date
    today = date.today().isoformat()
    events = db_manager.search_events(user_id=1, date=today)
    return {
        "date": today,
        "events": events,
        "count": len(events)
    }

# ============================================================================
# CHAT HISTORY ENDPOINTS (Message Display)
# ============================================================================

@app.get("/chat/history")
async def get_chat_history(
    user_id: str,
    thread_id: Optional[str] = None,
    limit: int = 100,
    api_key: str = Depends(get_api_key)
):
    """
    Get chat history for a user.
    - user_id: Required. The user's unique identifier (string or numeric).
    - thread_id: Optional. If provided, returns messages from that thread only.
    - limit: Max messages to return (default: 100)
    """
    # Convert user_id to int if numeric, otherwise use as-is
    uid = int(user_id) if user_id.isdigit() else 1
    messages = db_manager.get_chat_history(uid, thread_id, limit)
    return {
        "user_id": user_id,
        "thread_id": thread_id,
        "messages": messages,
        "count": len(messages)
    }

@app.get("/chat/threads")
async def get_user_threads(
    user_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get all conversation threads for a user.
    Returns thread IDs with their last message time and message count.
    Use this to show a list of past conversations.
    """
    uid = int(user_id) if user_id.isdigit() else 1
    threads = db_manager.get_user_threads(uid)
    return {
        "user_id": user_id,
        "threads": threads,
        "count": len(threads)
    }


@app.get("/health")
async def health_check():
    """Service health check."""
    return {"status": "healthy", "service": "ched-agentic-backend"}

@app.delete("/chat/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    user_id: str = "1",
    api_key: str = Depends(get_api_key)
):
    """
    Delete a specific conversation thread and its history.
    """
    uid = int(user_id) if user_id.isdigit() else 1
    success = db_manager.delete_chat_thread(uid, thread_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete thread")
    return {"status": "success", "thread_id": thread_id}

if __name__ == "__main__":
    import uvicorn
    # If API_KEY is not set, warn the user
    if "API_KEY" not in os.environ:
        print("WARNING: API_KEY environment variable not set. Using 'default-secret-key'.")
    
    # When running as a script, we use the app object.
    # If you want reload=True, you'd need the string path "ai_scheduler.api:app"
    uvicorn.run(app, host="0.0.0.0", port=8000)
