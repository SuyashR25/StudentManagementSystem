import datetime
from typing import List
from langchain_core.tools import tool
from models import ScheduleEvent


def get_calendar_service():
    """Placeholder for removed service."""
    return None

def get_current_calendar_events(days: int = 14) -> List[dict]:
    """Mock for removed service."""
    return []

def create_calendar_event(event: ScheduleEvent) -> dict:
    """Mock for removed service."""
    return {"success": False, "error": "Google Calendar API disabled."}


@tool
def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format. Useful for resolving relative dates like 'tomorrow'."""
    return datetime.datetime.now().strftime("%Y-%m-%d")


@tool
def list_calendar_events(limit: int = 10, user_id: int = 1) -> str:
    """Lists the next few upcoming calendar events to get an overview of the schedule."""
    from database import db_manager
    events = db_manager.get_upcoming_events(user_id=user_id, limit=limit)
    if not events: return "No upcoming events found."
    return "\n".join([f"ID: {e['id']} | {e['title']} | {e['start_datetime']} to {e['end_datetime']}" for e in events])


@tool
def search_calendar(query: str = None, date: str = None, user_id: int = 1) -> str:
    """
    Search for specific events in the calendar.
    Provide a 'query' (keyword) to search by title/desc, or a 'date' (YYYY-MM-DD) to see events on a specific day.
    """
    from database import db_manager
    events = db_manager.search_events(user_id=user_id, query=query, date=date)
    if not events: return f"No events found for query='{query}' date='{date}'"
    return "\n".join([f"ID: {e['id']} | {e['title']} | {e['start_datetime']} to {e['end_datetime']}" for e in events])

@tool
def add_event(title: str, start_datetime: str, end_datetime: str, priority: str = "Medium", category: str = "General", description: str = "", user_id: int = 1) -> str:
    """
    Adds a new event to the calendar.
    - title: Title of the event
    - start_datetime: ISO format string (YYYY-MM-DDTHH:MM:SS)
    - end_datetime: ISO format string
    - priority: High, Medium, or Low
    - category: Event category
    """
    from database import db_manager
    from models import ScheduleEvent
    event = ScheduleEvent(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        priority=priority,
        category=category,
        description=description,
        source="agent"
    )
    added = db_manager.add_schedule_event(event, user_id=user_id)
    if not added:
        return f"Skipped: Event '{title}' at {start_datetime} is already in the calendar."
    return f"Successfully added event: {title}"

@tool
def delete_calendar_event(event_id: int, user_id: int = 1) -> str:
    """Deletes a specific event from the calendar by its ID."""
    from database import db_manager
    success = db_manager.delete_event(event_id, user_id=user_id)
    if success:
        return f"Successfully deleted event with ID: {event_id}"
    return f"Failed to delete event: ID {event_id} not found."

@tool
def delete_events_on_date(date_str: str, user_id: int = 1) -> str:
    """Deletes all events scheduled for a specific date (YYYY-MM-DD)."""
    from database import db_manager
    count = db_manager.delete_events_by_date(date_str, user_id=user_id)
    return f"Successfully deleted {count} events on {date_str}"

@tool
def update_calendar_event(event_id: int, updates: dict, user_id: int = 1) -> str:
    """
    Updates an existing event's fields.
    - event_id: ID of the event to update
    - updates: Dictionary of fields to update (title, start_datetime, end_datetime, priority, category, description)
    """
    from database import db_manager
    success = db_manager.update_event(event_id, user_id=user_id, updates=updates)
    if success:
        return f"Successfully updated event with ID: {event_id}"
    return f"Failed to update event: ID {event_id} not found."

@tool
def clear_full_calendar(user_id: int = 1) -> str:
    """Wipes the entire calendar database. Use with extreme caution when the user wants to delete EVERYTHING."""
    from database import db_manager
    count = db_manager.clear_all_events(user_id=user_id)
    return f"Successfully wiped the calendar. {count} events were removed."


@tool
def list_available_courses() -> str:
    """Lists all courses available in the university catalog for enrollment."""
    from database import db_manager
    courses = db_manager.get_all_courses()
    if not courses: return "No courses found in the catalog."
    return "\n".join([f"ID: {c['id']} | {c['name']} ({c['code']}) | Credits: {c['credits']} | Semester: {c.get('semester', 'N/A')}" for c in courses])


@tool
def enroll_student_in_course(course_id: int = None, course_name: str = None) -> str:
    """
    Enrolls the student in a specific course from the catalog.
    - course_id: The unique ID of the course to enroll in (preferred).
    - course_name: The name of the course (will look up the ID from catalog).
    You must provide either course_id OR course_name.
    """
    from database import db_manager
    
    # If only course_name provided, look up the ID from catalog
    if course_id is None and course_name:
        all_courses = db_manager.get_all_courses()
        for c in all_courses:
            if course_name.lower() in c['name'].lower() or course_name.lower() in c.get('code', '').lower():
                course_id = c['id']
                break
        if course_id is None:
            return f"Could not find a course matching '{course_name}' in the catalog."
    
    
    if course_id is None:
        return "Please provide either a course_id or course_name to enroll."
        
    # Verify course_id exists in catalog
    all_courses = db_manager.get_all_courses()
    # If we didn't just fetch them for name lookup:
    if not (course_id is None and course_name): 
        # (Optimize: we could cache or reload, but for safety let's check)
        # Actually all_courses is local scope, so if we fetched it above, we have it. 
        # But if we entered with course_id, we didn't fetch it.
        pass
        
    # Re-fetch or reuse
    if 'all_courses' not in locals():
        all_courses = db_manager.get_all_courses()
        
    course_match = next((c for c in all_courses if c['id'] == course_id), None)
    if not course_match:
        return f"Error: Course ID {course_id} not found in the catalog. Please use 'list_available_courses' to verify IDs."
    
    # Perform the enrollment
    success = db_manager.enroll_in_course(user_id=1, course_id=course_id)
    if success:
        return f"Successfully enrolled in course ID {course_id}: {course_match['name']}."
    else:
        return f"Enrollment skipped: You are likely already enrolled in course ID {course_id}: {course_match['name']}."


@tool
def unenroll_student_from_course(course_id: int = None, course_name: str = None) -> str:
    """
    Removes the student's enrollment from a specific course.
    - course_id: The unique ID of the course to unenroll from (preferred).
    - course_name: The name of the course (will look up the ID).
    You must provide either course_id OR course_name.
    """
    from database import db_manager
    import sqlite3
    
    # If only course_name provided, look up the ID
    if course_id is None and course_name:
        courses = db_manager.get_enrolled_courses(user_id=1)
        for c in courses:
            if course_name.lower() in c['name'].lower() or course_name.lower() in c['code'].lower():
                course_id = c['id']
                break
        if course_id is None:
            return f"Could not find a course matching '{course_name}' in your enrolled courses."
    
    if course_id is None:
        return "Please provide either a course_id or course_name to unenroll."
    
    # Perform the unenrollment
    success = db_manager.unenroll_from_course(user_id=1, course_id=course_id)
    if success:
        return f"Successfully unenrolled from course ID {course_id}."
    else:
        return f"Failed to unenroll: Course ID {course_id} was not found in your enrollment list."


@tool
def get_my_enrolled_courses() -> str:
    """Returns the list of courses the student is currently enrolled in with their status and grades."""
    from database import db_manager
    courses = db_manager.get_enrolled_courses(user_id=1)
    if not courses:
        return "You are not enrolled in any courses."
    result = []
    for c in courses:
        grade_str = f" | Grade: {c['grade']}" if c.get('grade') else ""
        status_str = f" | Status: {c['status']}" if c.get('status') else ""
        sem_str = f" | Semester: {c['semester']}" if c.get('semester') else ""
        result.append(f"ID: {c['id']} | {c['name']} ({c['code']}) | Credits: {c['credits']}{sem_str}{grade_str}{status_str}")
    return "\n".join(result)


@tool
def retrieve_from_docs(query: str, user_id: int = 1) -> str:
    """
    Searches uploaded academic documents (PDFs, PPTs) for relevant information.
    Use this tool when you need to answer questions based on the content of user-uploaded files.
    """
    from rag_engine import vector_manager
    try:
        # Enforce string user_id for consistency
        results = vector_manager.retrieve(query, user_id=str(user_id), k=5)
        if not results:
            return "No relevant information found in the documents."
        
        snippets = []
        for doc, score in results:
            snippets.append(f"[Source: {doc.metadata.get('source_file', 'unknown')}]\n{doc.page_content}")
        
        return "\n\n---\n\n".join(snippets)
    except Exception as e:
        return f"Error retrieving documents: {str(e)}"
