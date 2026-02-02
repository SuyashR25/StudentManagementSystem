import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Courses from './pages/Courses';
import Calendar from './pages/Calendar';
import Grades from './pages/Grades';
import FocusTimer from './pages/FocusTimer';
import Settings from './pages/Settings';
import AIFloatingButton from './components/AIFloatingButton';
import AiChat from './components/AiChat';
import './App.css';

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/courses" element={<Courses />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/grades" element={<Grades />} />
            <Route path="/focus" element={<FocusTimer />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>

        <AIFloatingButton onClick={() => setIsChatOpen(true)} />
        <AiChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />

        {/* Background Decorative Blobs */}
        <div className="bg-blob blob-1"></div>
        <div className="bg-blob blob-2"></div>
      </div>
    </Router>
  );
}

export default App;
