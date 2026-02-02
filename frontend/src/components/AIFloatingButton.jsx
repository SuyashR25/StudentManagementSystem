import { Bot } from 'lucide-react';
import './AIFloatingButton.css';

const AIFloatingButton = ({ onClick }) => {
    return (
        <button className="ai-floating-btn animate-float" onClick={onClick}>
            <span className="ping-effect"></span>
            <Bot size={28} className="bot-icon" />
            <span className="tooltip">Ask AI Assistant</span>
        </button>
    );
};

export default AIFloatingButton;
