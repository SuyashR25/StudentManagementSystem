import os
import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models import MultiAgentState, RAGOutput
from llm_config import rag_llm
from rag_engine import vector_manager
import json as json_lib

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

def rag_agent(state: MultiAgentState) -> dict:
    """
    RAG Agent: Handles document retrieval and synthesis.
    Chunks, indexes, and retrieves from uploaded files.
    """
    try:
        query = state.get("user_query", "")
        pdf_paths = state.get("pdf_paths", [])
        user_id = state.get("user_id", "default")
        
        # 1. Direct Context Injection (for current files)
        direct_context = []
        if pdf_paths:
            print(f"DEBUG: RAG Agent loading context from {len(pdf_paths)} files. Paths: {pdf_paths}")
            for path in pdf_paths:
                 actual_path = path
                 if not os.path.exists(actual_path):
                     # Try in upload dir
                     actual_path = os.path.join(UPLOAD_DIR, os.path.basename(path))
                 
                 if os.path.exists(actual_path):
                     text = vector_manager.load_document_text(actual_path)
                     if text:
                         # Limit size to prevent overflow (e.g., 5k chars)
                         if len(text) > 5000: text = text[:5000] + "...(truncated)"
                         direct_context.append(f"--- DOCUMENT: {os.path.basename(actual_path)} ---\n{text}")
                     else:
                         print(f"DEBUG: WARNING - Document text is EMPTY for {actual_path}")
                 else:
                     print(f"DEBUG: ERROR - File not found: {path} (checked {actual_path} too)")
            
            # Ensure documents are ingested for future retrieval
            vector_manager.ingest_documents(pdf_paths, user_id=user_id)
            
        parser = PydanticOutputParser(pydantic_object=RAGOutput)
        
        # 2. Retrieved Context (for history)
        retrieved = []
        if vector_manager.vector_store:
            retrieved = vector_manager.retrieve(query, user_id=user_id, k=5)
            
        chunks = []
        scores = []
        sources = []
        
        for doc, score in retrieved:
            chunks.append(doc.page_content)
            scores.append(float(1 - score))
            sources.append(doc.metadata.get("source_file", "unknown"))
            
        retrieved_text = "\n\n---\n\n".join(chunks) if chunks else "No relevant historical documents found."
        
        # Combine
        context = f"=== CURRENT UPLOADED FILES ===\n" + "\n".join(direct_context) + f"\n\n=== RETRIEVED HISTORY ===\n{retrieved_text}"
        
        today_now = datetime.datetime.now()
        today_val = today_now.strftime("%Y-%m-%d")
        day_name = today_now.strftime("%A")

        # Define Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a RAG agent specialized in extracting and synthesizing information from academic documents.
    Your goal is to extract structured data (deadlines, tasks, timetables, events) from the retrieved documents so they can be scheduled.

    Retrieved Context:
    {context}

    Today's Date: {today} ({day_name})

    Rules:
    1. Extract ALL recurring classes, labs, and tutorials from the context into the 'extracted_timetable' list.
    2. LOOK FOR TABLE PATTERNS: If you see "Monday", "Tuesday", etc. followed by times (8:30-9:25), these are CLASSES.
    3. If there are NO classes found, return an empty list: [].
    4. For 'extracted_timetable' entries, include the course name, day of week, start_time, and end_time precisely as found in the text.
    5. Provide a helpful synthesized answer summarizing exactly how many items you found.

    You MUST respond with a JSON block.
    
    Example of extracted_timetable:
    [
      {{"course": "Automata Theory", "day": "Monday", "start_time": "08:30", "end_time": "09:25", "location": "CLT 111"}},
      {{"course": "Digital Systems", "day": "Monday", "start_time": "09:30", "end_time": "10:25", "location": "CLT 105"}}
    ]

    You MUST respond with valid JSON in this format:
    {{
      "synthesized_answer": "Extracted X classes and Y deadlines.",
      "extracted_deadlines": [
         {{"title": "Assignment", "due_date": "YYYY-MM-DD", "description": "..."}}
      ],
      "extracted_tasks": [],
      "extracted_timetable": [
        {{"course": "Course Name", "day": "Monday", "start_time": "HH:MM", "end_time": "HH:MM", "location": "Room"}}
      ],
      "extracted_events": []
    }}
    """),
            ("human", "Query: {query}")
        ])
        
        # Initial invocation
        print(f"DEBUG: RAG Agent invoking LLM for query: {query[:50]}...")
        response = rag_llm.invoke(prompt.format(
            query=query,
            context=context,
            today=today_val,
            day_name=day_name
        ))
        
        # Parsing Logic
        content = response.content if isinstance(response.content, str) else str(response.content)
        print(f"DEBUG: RAG Agent Raw LLM Response FULL: {content}")
        clean_content = content.strip()
        
        # Robust JSON extraction
        json_str = ""
        if "```json" in clean_content:
            import re
            match = re.search(r"```json(.*?)```", clean_content, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
        
        if not json_str:
            # Fallback: look for generic { }
            start_index = clean_content.find("{")
            end_index = clean_content.rfind("}") + 1
            if start_index != -1 and end_index > start_index:
                json_str = clean_content[start_index:end_index]
            else:
                json_str = clean_content

        try:
            data = json_lib.loads(json_str)
            parsed = RAGOutput(**data)
            print(f"DEBUG: RAG Agent successfully extracted {len(parsed.extracted_timetable)} classes")
        except Exception as e:
            print(f"DEBUG: RAG Agent parsing ERROR: {e}")
            # Try partial cleaning
            try:
                parsed = parser.parse(clean_content)
            except:
                # Fallback
                parsed = RAGOutput(
                    synthesized_answer=content, # Use raw content as answer
                    extracted_deadlines=[]
                )
            
        parsed.retrieved_chunks = chunks
        parsed.relevance_scores = scores
        parsed.source_documents = sources
        
        return {"rag_output": parsed.model_dump()}

    except Exception as e:
        # Global fallback prevents 500 error
        print(f"RAG Agent Error: {e}")
        fallback = RAGOutput(
            synthesized_answer=f"I encountered an error processing the document: {str(e)}",
            retrieved_chunks=[],
            source_documents=[]
        )
        return {"rag_output": fallback.model_dump(), "error": str(e)}
