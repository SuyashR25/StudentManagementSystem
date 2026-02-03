# 🎓 EduTrack - AI-Powered Academic Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge)](https://github.com/langchain-ai/langgraph)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

EduTrack is an intelligent multi-agent AI system designed to help students manage their academic life. It combines **document understanding**, **smart scheduling**, and **conversational AI** to automatically extract timetables, deadlines, and events from uploaded documents (PDFs, syllabi) and schedule them into your calendar.

## ✨ Features

### 🤖 Multi-Agent Architecture
- **Orchestrator Agent** - Routes user queries to the appropriate specialized agent
- **RAG Agent** - Extracts information from uploaded documents (PDFs, timetables, syllabi)
- **Scheduler Agent** - Manages calendar events, creates/updates/deletes schedule items
- **Chat Agent** - Handles general conversations and Q&A
- **Academic Agent** - Manages GPA calculations, course enrollments, and academic history
- **Verifier Agent** - Validates scheduling decisions and detects conflicts

### 📅 Smart Calendar Management
- Automatic extraction of class schedules from timetable PDFs
- Intelligent conflict detection and resolution
- Event CRUD operations via natural language
- Date-range filtering and search functionality

### 📄 Document Intelligence (RAG)
- Upload PDFs and PowerPoint files
- Automatic chunking and vector indexing using Pinecone
- Context-aware retrieval for Q&A
- Timetable and deadline extraction

### ✅ Todo Management
- Create, update, and delete todos
- Priority and tag-based organization
- Due date tracking

---

## 🏗️ Project Structure

```
proto/
├── ai_scheduler/                # Backend - Multi-Agent System
│   ├── agents/                  # Agent implementations
│   │   ├── orchestrator.py      # Query routing agent
│   │   ├── rag.py               # Document retrieval agent
│   │   ├── scheduler.py         # Calendar management agent
│   │   ├── chat.py              # Conversational agent
│   │   ├── academic.py          # GPA & enrollment agent
│   │   └── verifier.py          # Conflict verification agent
│   ├── api.py                   # FastAPI endpoints
│   ├── database.py              # SQLite database manager
│   ├── models.py                # Pydantic data models
│   ├── llm_config.py            # LLM configuration
│   ├── rag_engine.py            # Vector store & retrieval
│   ├── utils.py                 # Tool functions for agents
│   └── uploads/                 # Uploaded documents storage
│
├── frontend/                    # Frontend - React + Vite
│   ├── src/                     # React components
│   ├── package.json             # Dependencies
│   └── vite.config.js           # Vite configuration
│
├── data/                        # Database files
├── .env                         # API keys configuration
└── .env.local                   # Local overrides
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- API keys for:
  - OpenRouter (LLM API)
  - HuggingFace (Embeddings)
  - Pinecone (Vector Store)
  - Google API (optional)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd proto
   ```

2. **Create a Python virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install fastapi uvicorn langchain langchain-openai langchain-huggingface langgraph pydantic python-dotenv pinecone-client pypdf python-multipart
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
   PINECONE_API_KEY=your_pinecone_api_key
   GOOGLE_API_KEY=your_google_api_key  # Optional
   ```

5. **Start the backend server**
   ```bash
   cd ai_scheduler
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

---

## 📡 API Reference

### Authentication
All endpoints require an API key header:
```
X-API-Key: your-api-key
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/query` | Process a natural language query with AI agents |
| `POST` | `/upload` | Upload a document (PDF/PPT) for RAG processing |
| `GET` | `/formats` | Get supported file formats |

### Calendar Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/events` | Get calendar events (with optional date range) |
| `POST` | `/events` | Create a new calendar event |
| `PUT` | `/events/{id}` | Update an existing event |
| `DELETE` | `/events/{id}` | Delete an event |
| `DELETE` | `/events` | Clear all events |

### Todo Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/todos` | Get all todos for a user |
| `POST` | `/todos` | Create a new todo |
| `PUT` | `/todos/{id}` | Update a todo |
| `DELETE` | `/todos/{id}` | Delete a todo |

### Course Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/courses` | Get all available courses |
| `GET` | `/enrolled-courses` | Get user's enrolled courses |
| `POST` | `/enroll` | Enroll in a course |
| `DELETE` | `/enroll/{id}` | Drop a course |

---

## 💬 Usage Examples

### Upload a Timetable and Schedule Classes
```
User: "Schedule all classes from this timetable"
+ Upload: TimeTable_CSE_4thSem.pdf

→ RAG Agent extracts class schedule from PDF
→ Scheduler Agent creates recurring calendar events
→ Response: "I've scheduled 15 classes from your timetable!"
```

### Natural Language Calendar Management
```
User: "Delete all events on Monday"
→ Scheduler Agent removes all Monday events

User: "What do I have tomorrow?"
→ Calendar Agent shows upcoming events

User: "Add a study session for Math on Friday at 3 PM"
→ Scheduler Agent creates the event
```

### GPA Planning (Academic Agent)
```
User: "What SGPA do I need to reach 8.5 CGPA?"
→ Academic Agent calculates required grades
```

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend Framework** | FastAPI |
| **AI Orchestration** | LangGraph |
| **LLM Provider** | OpenRouter (GPT-OSS-120B) |
| **Embeddings** | HuggingFace (all-MiniLM-L6-v2) |
| **Vector Store** | Pinecone |
| **Database** | SQLite |
| **Frontend** | React 19 + Vite |
| **Styling** | Custom CSS |
| **Charts** | Recharts |

---

## 🔧 Configuration

### LLM Configuration (`llm_config.py`)
- Modify model selection and parameters
- Add/remove agent tools
- Configure embeddings

### Database Configuration (`database.py`)
- SQLite databases stored in `/data` directory
- Separate databases for user data and agent checkpoints

---

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Important Notes

- **API Keys**: Never commit your `.env` file. Use `.env.local` for local overrides.
- **CORS**: The backend allows all origins by default. Configure appropriately for production.
- **Rate Limits**: Be mindful of API rate limits from OpenRouter and Pinecone.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for students everywhere
</p>
