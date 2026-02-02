import { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Settings2, ExternalLink, Sparkles, Flame, SkipForward } from 'lucide-react';
import './FocusTimer.css';

const FocusTimer = () => {
    const [time, setTime] = useState(25 * 60); // 25 minutes in seconds
    const [isRunning, setIsRunning] = useState(false);
    const [sessionName, setSessionName] = useState('Mastering Calculus Derivatives');
    const [streak, setStreak] = useState(3);
    const [totalFocus, setTotalFocus] = useState('45m');
    const intervalRef = useRef(null);

    useEffect(() => {
        if (isRunning && time > 0) {
            intervalRef.current = setInterval(() => {
                setTime((prev) => prev - 1);
            }, 1000);
        } else if (time === 0) {
            setIsRunning(false);
        }

        return () => clearInterval(intervalRef.current);
    }, [isRunning, time]);

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const toggleTimer = () => {
        setIsRunning(!isRunning);
    };

    const resetTimer = () => {
        setIsRunning(false);
        setTime(25 * 60);
    };

    const progress = ((25 * 60 - time) / (25 * 60)) * 100;
    const circumference = 2 * Math.PI * 140;
    const strokeDashoffset = circumference - (progress / 100) * circumference;

    return (
        <div className="focus-page">
            <div className="focus-header">
                <div className="focus-logo">
                    <Sparkles size={22} />
                    <span>Zen Focus</span>
                </div>
                <div className="focus-status">
                    <span className="ai-tutor-badge">
                        <Sparkles size={14} />
                        AI Tutor Ready
                    </span>
                    <div className="user-avatar">
                        <span>👤</span>
                    </div>
                    <button className="menu-dots">⋮⋮</button>
                </div>
            </div>

            <div className="focus-content">
                <div className="session-label">
                    <span className="label-dot"></span>
                    <input
                        type="text"
                        value={sessionName}
                        onChange={(e) => setSessionName(e.target.value)}
                        className="session-input"
                    />
                    <button className="edit-btn">✏️</button>
                </div>

                <div className="timer-section">
                    <div className="timer-container">
                        <svg className="timer-ring" viewBox="0 0 320 320">
                            <circle
                                cx="160"
                                cy="160"
                                r="140"
                                fill="none"
                                stroke="rgba(255,255,255,0.05)"
                                strokeWidth="8"
                            />
                            <circle
                                cx="160"
                                cy="160"
                                r="140"
                                fill="none"
                                stroke="url(#timerGradient)"
                                strokeWidth="8"
                                strokeLinecap="round"
                                strokeDasharray={circumference}
                                strokeDashoffset={strokeDashoffset}
                                transform="rotate(-90 160 160)"
                                className="progress-ring"
                            />
                            <defs>
                                <linearGradient id="timerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor="var(--primary)" />
                                    <stop offset="100%" stopColor="var(--accent)" />
                                </linearGradient>
                            </defs>
                        </svg>
                        <div className="timer-display">
                            <span className="timer-value">{formatTime(time)}</span>
                            <span className="timer-label">FOCUS SESSION</span>
                        </div>
                    </div>

                    <div className="timer-controls">
                        <button className="control-btn reset" onClick={resetTimer}>
                            <RotateCcw size={20} />
                        </button>
                        <button
                            className={`control-btn primary ${isRunning ? 'pause' : 'play'}`}
                            onClick={toggleTimer}
                        >
                            {isRunning ? <Pause size={24} /> : <Play size={24} />}
                            <span>{isRunning ? 'Pause' : 'Start'}</span>
                        </button>
                        <button className="control-btn settings">
                            <Settings2 size={20} />
                        </button>
                    </div>
                </div>

                <div className="help-card glass-card">
                    <div className="help-icon">
                        <Sparkles size={20} />
                    </div>
                    <div className="help-content">
                        <h4>
                            Stuck on a concept?
                            <ExternalLink size={14} />
                        </h4>
                        <p>Ask your AI tutor for a quick explanation without leaving your focus zone.</p>
                        <a href="#" className="help-link">Chat now →</a>
                    </div>
                </div>
            </div>

            <div className="focus-footer">
                <div className="streak-info">
                    <Flame size={18} className="flame-icon" />
                    <span>{streak} Days</span>
                </div>
                <div className="total-focus">
                    <span>Focus</span>
                    <strong>{totalFocus}</strong>
                </div>
                <div className="music-controls">
                    <button className="music-skip">
                        <SkipForward size={14} />
                    </button>
                    <span className="music-label">Lofi Study</span>
                    <button className="music-pause">
                        <Pause size={14} />
                    </button>
                    <button className="music-next">
                        <SkipForward size={14} />
                    </button>
                </div>
                <button className="focus-mode-btn">
                    <Sparkles size={16} />
                </button>
            </div>
        </div>
    );
};

export default FocusTimer;
