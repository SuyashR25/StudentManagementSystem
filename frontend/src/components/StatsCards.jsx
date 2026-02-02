import { TrendingUp, Award, GraduationCap, MapPin, Clock } from 'lucide-react';
import './StatsCards.css';

export const CGPACard = ({ cgpa = 0.0, maxCgpa = 4.0, trend = 'Consistent improvement' }) => {
    const percentage = (cgpa / maxCgpa) * 100;

    return (
        <div className="stat-card glass-card cgpa-card">
            <div className="card-bg-icon">
                <GraduationCap size={120} />
            </div>
            <h3 className="card-label">Academic Performance</h3>

            <div className="cgpa-ring">
                <svg viewBox="0 0 100 100" className="progress-ring">
                    <circle
                        cx="50"
                        cy="50"
                        r="42"
                        fill="none"
                        stroke="rgba(255,255,255,0.05)"
                        strokeWidth="8"
                    />
                    <circle
                        cx="50"
                        cy="50"
                        r="42"
                        fill="none"
                        stroke="url(#cgpaGradient)"
                        strokeWidth="8"
                        strokeLinecap="round"
                        strokeDasharray={`${percentage * 2.64} 264`}
                        transform="rotate(-90 50 50)"
                        className="progress-circle"
                    />
                    <defs>
                        <linearGradient id="cgpaGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="var(--primary)" />
                            <stop offset="100%" stopColor="var(--accent)" />
                        </linearGradient>
                    </defs>
                </svg>
                <div className="cgpa-value">
                    <span className="cgpa-number">{cgpa === 0 ? '--' : cgpa.toFixed(1)}</span>
                    <span className="cgpa-max">/ {maxCgpa} CGPA</span>
                </div>
            </div>

            <div className="cgpa-badge">
                <TrendingUp size={14} />
                <span>Top 10% of class</span>
            </div>
            <p className="card-subtitle">{trend}</p>
        </div>
    );
};

export const DegreeProgressCard = ({
    completedCredits = 0,
    totalCredits = 120,
    coreCredits = '0 / 50',
    electiveCredits = '0 / 70',
    standing = 'Standing TBD'
}) => {
    const percentage = totalCredits > 0 ? Math.round((completedCredits / totalCredits) * 100) : 0;

    return (
        <div className="stat-card glass-card degree-card">
            <div className="card-header">
                <div>
                    <h3 className="card-title">Degree Progress</h3>
                    <p className="card-subtitle">Computer Science B.S.</p>
                </div>
                <div className="card-icon-badge">
                    <Award size={20} />
                </div>
            </div>

            <div className="progress-section">
                <div className="progress-header">
                    <span className="credits-display">
                        <strong>{completedCredits}</strong>
                        <span className="credits-divider">/ {totalCredits}</span>
                    </span>
                    <span className="percentage-badge">{percentage}% Complete</span>
                </div>
                <div className="progress-bar-container">
                    <div
                        className="progress-bar-fill"
                        style={{ width: `${percentage}%` }}
                    />
                </div>
                <p className="progress-note">{standing}</p>
            </div>

            <div className="credits-grid">
                <div className="credit-box">
                    <p className="credit-label">Core Credits</p>
                    <p className="credit-value">{coreCredits}</p>
                </div>
                <div className="credit-box">
                    <p className="credit-label">Electives</p>
                    <p className="credit-value">{electiveCredits}</p>
                </div>
            </div>
        </div>
    );
};

export const NextClassCard = ({
    title = 'No class scheduled',
    time = '--:--',
    location = 'TBD',
    imageUrl = 'https://images.unsplash.com/photo-1523580846011-d3a5bc25702b?w=600&q=80'
}) => {
    return (
        <div className="stat-card next-class-card">
            <div
                className="class-bg-image"
                style={{
                    backgroundImage: `url('${imageUrl}')`
                }}
            />
            <div className="class-overlay" />
            <div className="class-content">
                <span className="class-badge">Next Class</span>
                <h3 className="class-title">{title}</h3>
                <div className="class-details">
                    <div className="class-detail">
                        <Clock size={18} />
                        <span>{time}</span>
                    </div>
                    <div className="class-detail">
                        <MapPin size={18} />
                        <span>{location}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
