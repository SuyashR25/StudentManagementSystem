from typing import List, Optional, Literal, Annotated, TypedDict
from enum import Enum
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

class AgentType(str, Enum):
    """Types of agents the orchestrator can route to"""
    RAG = "rag"
    SCHEDULER = "scheduler"
    CHAT = "chat"
    CALENDAR = "calendar"
    ACADEMIC = "academic"


class CourseGrade(BaseModel):
    """Individual course grade info"""
    course_code: str
    credits: float
    grade_point: Optional[float] = None  # Points (e.g., 4.0)
    letter_grade: Optional[str] = None   # Letter (e.g., "A")


class SemesterRecord(BaseModel):
    """Record of a single semester"""
    semester_name: str
    courses: List[CourseGrade]
    sgpa: Optional[float] = None


class AcademicHistory(BaseModel):
    """User's full academic history"""
    semesters: List[SemesterRecord] = Field(default_factory=list)
    cumulative_credits: float = 0.0
    cgpa: float = 0.0


class GPAStrategyOutput(BaseModel):
    """Structured output from GPA Strategist"""
    current_cgpa: float
    target_cgpa: float
    required_sgpa: Optional[float] = None
    is_feasible: bool
    feasibility_message: str
    suggested_grade_combinations: List[dict] = Field(default_factory=list)
    optimization_rationale: str


class OrchestratorOutput(BaseModel):
    """Structured output from Orchestrator Agent"""
    intent: AgentType = Field(description="The detected intent/agent to route to")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for routing decision")
    extracted_entities: dict = Field(default_factory=dict, description="Extracted entities from user query")
    query_summary: str = Field(description="Summarized/cleaned version of user query")
    requires_context: bool = Field(default=False, description="Whether RAG context is needed")
    reasoning: str = Field(description="Brief reasoning for the routing decision")


class TimetableEntry(BaseModel):
    """Specific entry for a recurring class or lab"""
    course: str
    day: str
    start_time: str
    end_time: str
    location: Optional[str] = None

class EventEntry(BaseModel):
    """Specific entry for a one-time event or deadline"""
    title: str
    date: str
    time: Optional[str] = None
    description: Optional[str] = None

class RAGOutput(BaseModel):
    """Structured output from RAG Agent"""
    synthesized_answer: str = Field(description="Synthesized answer from retrieved context")
    extracted_deadlines: List[dict] = Field(default_factory=list, description="Extracted deadline information")
    extracted_tasks: List[dict] = Field(default_factory=list, description="Extracted task information")
    extracted_timetable: List[dict] = Field(default_factory=list, description="Extracted recurring class/timetable information")
    extracted_events: List[dict] = Field(default_factory=list, description="Extracted one-time event information")
    # Internal fields populated by agent, not LLM
    retrieved_chunks: Optional[List[str]] = Field(default=None, description="Retrieved document chunks")
    relevance_scores: Optional[List[float]] = Field(default=None, description="Relevance scores for chunks")
    source_documents: Optional[List[str]] = Field(default=None, description="Source document names")


class ScheduleEvent(BaseModel):
    """Individual schedule event"""
    title: str = Field(description="Event title")
    start_datetime: str = Field(description="Start datetime in ISO format")
    end_datetime: str = Field(description="End datetime in ISO format")
    priority: Literal["High", "Medium", "Low"] = Field(default="Medium")
    category: str = Field(default="General", description="Event category (Study, Assignment, Exam, etc.)")
    description: str = Field(default="", description="Event description")
    source: str = Field(default="user", description="Source of the event (user, syllabus, etc.)")


class SchedulerOutput(BaseModel):
    """Structured output from Scheduler Agent - Proposed State"""
    proposed_events: List[ScheduleEvent] = Field(default_factory=list, description="Proposed new events")
    modified_events: List[dict] = Field(default_factory=list, description="Events to modify")
    deleted_event_ids: List[str] = Field(default_factory=list, description="Event IDs to delete")
    scheduling_rationale: str = Field(description="Rationale for proposed changes")
    conflicts_detected: List[str] = Field(default_factory=list, description="Detected scheduling conflicts")
    optimization_suggestions: List[str] = Field(default_factory=list, description="Suggestions for optimization")


class VerifierOutput(BaseModel):
    """Structured output from Verifier Agent"""
    is_valid: bool = Field(description="Whether the proposed changes are valid")
    conflicts: List[str] = Field(default_factory=list, description="List of conflicts found")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    approved_events: List[ScheduleEvent] = Field(default_factory=list, description="Approved events")
    approved_deletions: List[str] = Field(default_factory=list, description="Approved event IDs to delete")
    rejected_events: List[dict] = Field(default_factory=list, description="Rejected events with reasons")
    verification_notes: str = Field(description="Notes from verification process")


class ChatOutput(BaseModel):
    """Structured output from Chat Agent"""
    response: str = Field(description="The conversational response")
    sentiment: Literal["positive", "neutral", "negative"] = Field(default="neutral")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up actions")
    requires_action: bool = Field(default=False, description="Whether response requires user action")


class CurrentState(BaseModel):
    """Current state of the schedule system"""
    existing_events: List[dict] = Field(default_factory=list, description="Current calendar events")
    active_tasks: List[dict] = Field(default_factory=list, description="Active tasks/assignments")
    academic_history: AcademicHistory = Field(default_factory=AcademicHistory)
    user_preferences: dict = Field(default_factory=dict, description="User scheduling preferences")
    last_updated: str = Field(default="", description="Last update timestamp")


class MultiAgentState(TypedDict):
    """State shared across all agents"""
    messages: Annotated[list, add_messages]
    user_query: str
    user_id: str  # For multi-tenant document isolation
    orchestrator_output: Optional[dict]
    rag_output: Optional[dict]
    scheduler_output: Optional[dict]
    verifier_output: Optional[dict]
    chat_output: Optional[dict]
    academic_output: Optional[dict]
    current_state: Optional[dict]
    pdf_paths: List[str]
    final_response: str
    error: Optional[str]
    loop_count: int

class TodoItem(BaseModel):
    """Individual to-do item"""
    id: Optional[int] = None
    user_id: int
    text: str
    completed: bool = False
    due_date: Optional[str] = None
    priority: Optional[str] = None
    tag: Optional[str] = None
    created_at: Optional[str] = None
