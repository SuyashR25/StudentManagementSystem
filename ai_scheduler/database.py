from typing import List
import sqlite3
import json
import os
from models import AcademicHistory, SemesterRecord, CourseGrade, ScheduleEvent
from langgraph.checkpoint.sqlite import SqliteSaver

# Define central database paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

MAIN_DB_PATH = os.path.join(DATA_DIR, "users.db")
CHED_DB_PATH = os.path.join(DATA_DIR, "ched_user_data.db")
CHECKPOINT_DB_PATH = os.path.join(DATA_DIR, "multi_agent_checkpoints.db")

print(f"DEBUG: DatabaseManager using CHED_DB at: {CHED_DB_PATH}")

class DatabaseManager:
    """Manages persistent storage for academic records and schedules."""
    
    def __init__(self, main_db: str = MAIN_DB_PATH, secondary_db: str = CHED_DB_PATH):
        self.main_db = main_db
        self.secondary_db = secondary_db
        self._init_db()
    
    def _init_db(self):
        # Initialize AI-specific tables (Schedule, Chat) in the CHED database
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            print(f"DEBUG: Initializing/Checking tables in {self.secondary_db}")
            # Schedule Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    start_datetime TEXT,
                    end_datetime TEXT,
                    priority TEXT,
                    category TEXT,
                    description TEXT,
                    source TEXT
                )
            """)
            # Chat History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    thread_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    intent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Todo Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todo_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    due_date TEXT,
                    priority TEXT,
                    tag TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

        # Initialize main database tables for Enrollment
        with sqlite3.connect(self.main_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    credits INTEGER,
                    semester INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_id INTEGER NOT NULL,
                    grade REAL,
                    status TEXT DEFAULT 'active',
                    UNIQUE(user_id, course_id)
                )
            """)
            conn.commit()

    def add_academic_record(self, record: SemesterRecord, user_id: int):
        """Unified method: Writes to the main dashboard database."""
        with sqlite3.connect(self.main_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            for course in record.courses:
                # 1. Ensure course exists in the global registry
                cursor.execute("SELECT id FROM courses WHERE code = ?", (course.course_code,))
                res = cursor.fetchone()
                if res:
                    course_id = res[0]
                else:
                    cursor.execute(
                        "INSERT INTO courses (name, code, credits, semester) VALUES (?, ?, ?, ?)",
                        (course.course_code, course.course_code, course.credits, 1)
                    )
                    course_id = cursor.lastrowid
                
                # 2. Record/Update enrollment for this user
                cursor.execute("""
                    INSERT OR REPLACE INTO user_courses (user_id, course_id, grade, status)
                    VALUES (?, ?, ?, ?)
                """, (user_id, course_id, course.grade_point, 'completed' if course.grade_point is not None else 'active'))
            conn.commit()

    def get_full_academic_history(self, user_id: int) -> AcademicHistory:
        """Unified method: Reads from the main dashboard database."""
        with sqlite3.connect(self.main_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Join user_courses with courses to get full history
            cursor.execute("""
                SELECT c.code, c.name, c.credits, c.semester, uc.grade
                FROM user_courses uc
                JOIN courses c ON uc.course_id = c.id
                WHERE uc.user_id = ?
            """, (user_id,))
            rows = cursor.fetchall()
            
            semesters_dict = {}
            total_credits = 0.0
            total_points = 0.0
            
            for row in rows:
                sem = f"Semester {row['semester']}"
                if sem not in semesters_dict:
                    semesters_dict[sem] = []
                
                course = CourseGrade(
                    course_code=row['code'],
                    credits=row['credits'],
                    grade_point=row['grade'],
                    letter_grade=None 
                )
                semesters_dict[sem].append(course)
                
                if row['grade'] is not None:
                    total_credits += row['credits']
                    total_points += (row['grade'] * row['credits'])
            
            history_records = []
            for name, courses in semesters_dict.items():
                record = SemesterRecord(semester_name=name, courses=courses)
                history_records.append(record)
            
            cgpa = (total_points / total_credits) if total_credits > 0 else 0.0
            
            # Use cumulative_credits to match models.py
            return AcademicHistory(
                semesters=history_records, 
                cumulative_credits=total_credits, 
                cgpa=cgpa
            )

    # --- Course Enrollment Methods ---

    def get_all_courses(self) -> List[dict]:
        """Returns the list of available courses from the JSON data file."""
        courses_file = os.path.join(DATA_DIR, "courses.json")
        if not os.path.exists(courses_file):
            return []
        with open(courses_file, "r") as f:
            return json.load(f)

    def get_enrolled_courses(self, user_id: int) -> List[dict]:
        """Fetch all courses a user is currently enrolled in (active status)."""
        with sqlite3.connect(self.main_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name, c.code, c.credits, uc.status, c.semester
                FROM user_courses uc
                JOIN courses c ON uc.course_id = c.id
                WHERE uc.user_id = ? AND uc.status = 'active'
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def enroll_in_course(self, user_id: int, course_id: int, course_name: str = None, course_code: str = None, credits: int = None) -> bool:
        """Enroll a user in a course. Ensures course exists and creates user_course entry."""
        with sqlite3.connect(self.main_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            
            # If course_id is provided, try to get code/name from catalogue if not provided
            if course_id and (not course_code or not course_name):
                catalogue = self.get_all_courses()
                match = next((c for c in catalogue if c['id'] == course_id), None)
                if match:
                    course_name = course_name or match['name']
                    course_code = course_code or match['code']
                    credits = credits or match['credits']

            if not course_code:
                # Last ditch: try to find by ID in existing courses table
                cursor.execute("SELECT code, name, credits FROM courses WHERE id = ?", (course_id,))
                res = cursor.fetchone()
                if res:
                    course_code, course_name, credits = res
                else:
                    return False # Can't enroll without course info

            # 1. Ensure course exists in central registry
            cursor.execute("SELECT id FROM courses WHERE code = ?", (course_code,))
            res = cursor.fetchone()
            if not res:
                cursor.execute(
                    "INSERT INTO courses (name, code, credits, semester) VALUES (?, ?, ?, ?)",
                    (course_name, course_code, credits or 3, 1)
                )
                db_course_id = cursor.lastrowid
            else:
                db_course_id = res[0]
                if course_name or credits:
                    cursor.execute(
                        "UPDATE courses SET name = COALESCE(?, name), credits = COALESCE(?, credits) WHERE id = ?",
                        (course_name, credits, db_course_id)
                    )

            # 2. Add or Activate enrollment
            # Check if already enrolled to return False (for tool feedback)
            cursor.execute("SELECT status FROM user_courses WHERE user_id = ? AND course_id = ?", (user_id, db_course_id))
            curr = cursor.fetchone()
            if curr and curr[0] == 'active':
                return False

            cursor.execute("""
                INSERT INTO user_courses (user_id, course_id, status)
                VALUES (?, ?, 'active')
                ON CONFLICT(user_id, course_id) DO UPDATE SET status = 'active'
            """, (user_id, db_course_id))
            
            conn.commit()
            return True

    def unenroll_from_course(self, user_id: int, course_id: int) -> bool:
        """Drop a course (unenroll)."""
        try:
            with sqlite3.connect(self.main_db, timeout=30.0) as conn:
                cursor = conn.cursor()
                # Try by ID first
                cursor.execute("""
                    DELETE FROM user_courses 
                    WHERE user_id = ? AND course_id = ?
                """, (user_id, course_id))
                if cursor.rowcount > 0:
                    conn.commit()
                    return True
                
                # If failed, it might be the Course Catalogue ID vs Database ID mismatch
                # Join with courses to find by catalogue ID (courses.id)
                cursor.execute("""
                    DELETE FROM user_courses 
                    WHERE user_id = ? AND course_id IN (SELECT id FROM courses WHERE id = ?)
                """, (user_id, course_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def add_schedule_event(self, event: ScheduleEvent, user_id: int) -> bool:
        """Adds a new event to the calendar, preventing duplicates."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            
            # 1. Idempotency Check: Don't add if the same user has the same title at the same time
            cursor.execute("""
                SELECT id FROM user_schedule 
                WHERE user_id = ? AND title = ? AND start_datetime = ?
            """, (user_id, event.title, event.start_datetime))
            
            if cursor.fetchone():
                print(f"DEBUG: Skipping duplicate event: '{event.title}' at {event.start_datetime}")
                return False

            # 2. Add New Event
            cursor.execute("""
                INSERT INTO user_schedule (user_id, title, start_datetime, end_datetime, priority, category, description, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, event.title, event.start_datetime, event.end_datetime, event.priority, event.category, event.description, event.source))
            conn.commit()
            print(f"DEBUG: Event added successfully. ID: {cursor.lastrowid}")
            return True

    def get_upcoming_events(self, user_id: int, limit: int = 50) -> List[dict]:
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Show events starting most recently or in the future first
            cursor.execute("SELECT * FROM user_schedule WHERE user_id = ? ORDER BY start_datetime DESC LIMIT ?", (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_events_by_range(self, user_id: int, start_date: str, end_date: str) -> List[dict]:
        """Get events strictly between two dates (inclusive)."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_schedule 
                WHERE user_id = ? AND ((start_datetime BETWEEN ? AND ?) OR (end_datetime BETWEEN ? AND ?))
                ORDER BY start_datetime ASC
            """, (user_id, start_date, end_date, start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]

    def search_events(self, user_id: int, query: str = None, date: str = None) -> List[dict]:
        """Search events by title keyword or specific date."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if date:
                # Search by date (YYYY-MM-DD prefix)
                cursor.execute("SELECT * FROM user_schedule WHERE user_id = ? AND start_datetime LIKE ? ORDER BY start_datetime ASC", (user_id, f"{date}%"))
            elif query:
                # Search by keyword
                cursor.execute("SELECT * FROM user_schedule WHERE user_id = ? AND (title LIKE ? OR description LIKE ?) ORDER BY start_datetime ASC", (user_id, f"%{query}%", f"%{query}%"))
            else:
                return self.get_upcoming_events(user_id)
            return [dict(row) for row in cursor.fetchall()]

    def update_event(self, event_id: int, user_id: int, updates: dict) -> bool:
        """Update specific fields of an event."""
        if not updates: return False
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            fields = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values())
            values.extend([event_id, user_id])
            cursor.execute(f"UPDATE user_schedule SET {fields} WHERE id = ? AND user_id = ?", values)
            conn.commit()
            return cursor.rowcount > 0

    def delete_event(self, event_id: int, user_id: int) -> bool:
        """Delete an event by ID."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_schedule WHERE id = ? AND user_id = ?", (event_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_events_by_date(self, date: str, user_id: int) -> int:
        """Delete all events starting on a specific date (YYYY-MM-DD)."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_schedule WHERE user_id = ? AND start_datetime LIKE ?", (user_id, f"{date}%"))
            conn.commit()
            return cursor.rowcount

    def clear_all_events(self, user_id: int) -> int:
        """Delete every event in the database for a user."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_schedule WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount

    # =========================================================================
    # CHAT HISTORY METHODS
    # =========================================================================

    def save_message(self, user_id: int, thread_id: str, role: str, message: str, intent: str = None):
        """Save a chat message (user or assistant)."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO chat_history (user_id, thread_id, role, message, intent)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, thread_id, role, message, intent))
            conn.commit()

    def delete_chat_thread(self, user_id: int, thread_id: str) -> bool:
        """Deletes all chat messages and schedule items associated with a thread."""
        try:
            # Delete messages from chat history
            with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM chat_history 
                    WHERE user_id = ? AND thread_id = ?
                """, (user_id, thread_id))
                conn.commit()
            
            # Delete items from scheduler if they came from this thread (source tracking)
            with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM user_schedule 
                    WHERE user_id = ? AND source = ?
                """, (user_id, thread_id))
                conn.commit()
                
            return True
        except Exception as e:
            print(f"Error deleting thread: {e}")
            return False

    def get_chat_history(self, user_id: int, thread_id: str = None, limit: int = 100) -> List[dict]:
        """
        Get chat history for a user.
        """
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if thread_id:
                cursor.execute("""
                    SELECT id, user_id, thread_id, role, message, intent, timestamp
                    FROM chat_history 
                    WHERE user_id = ? AND thread_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (user_id, thread_id, limit))
            else:
                cursor.execute("""
                    SELECT id, user_id, thread_id, role, message, intent, timestamp
                    FROM chat_history 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_user_threads(self, user_id: int) -> List[dict]:
        """Get all conversation threads for a user with their last message."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT thread_id, 
                       MAX(timestamp) as last_message_time,
                       COUNT(*) as message_count
                FROM chat_history 
                WHERE user_id = ?
                GROUP BY thread_id
                ORDER BY last_message_time DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_todos(self, user_id: int) -> List[dict]:
        """Fetch all todo items for a specific user."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, text, completed, due_date, priority, tag, created_at
                FROM todo_items
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_todo(self, user_id: int, text: str, due_date: str = None, priority: str = "Medium", tag: str = "General") -> int:
        """Add a new todo item."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO todo_items (user_id, text, due_date, priority, tag)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, text, due_date, priority, tag))
            conn.commit()
            return cursor.lastrowid

    def update_todo(self, todo_id: int, completed: bool = None, text: str = None) -> bool:
        """Update an existing todo item."""
        updates = []
        params = []
        if completed is not None:
            updates.append("completed = ?")
            params.append(1 if completed else 0)
        if text is not None:
            updates.append("text = ?")
            params.append(text)
        
        if not updates:
            return False
            
        params.append(todo_id)
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE todo_items 
                SET {", ".join(updates)}
                WHERE id = ?
            """, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo item."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM todo_items WHERE id = ?", (todo_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_todos(self, user_id: int) -> bool:
        """Remove all todos for a user."""
        with sqlite3.connect(self.secondary_db, timeout=30.0) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM todo_items WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0


from langgraph.checkpoint.memory import MemorySaver

# Global Database Manager
db_manager = DatabaseManager()

# Graph Persistence
# Using MemorySaver for stability with real-time streaming (astream_events).
# Note: Threads will be transient until persistent async checkpointer is stabilized.
checkpointer = MemorySaver()
