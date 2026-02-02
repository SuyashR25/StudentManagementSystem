import { Sparkles } from 'lucide-react';
import './AISummary.css';

const AISummary = ({
    positiveTrend = '0%',
    subject = 'N/A',
    recommendation = 'No new recommendations from your AI assistant yet.'
}) => {
    return (
        <div className="ai-summary glass-card">
            <div className="ai-gradient-bg"></div>
            <div className="ai-icon">
                <Sparkles size={20} className="sparkle-icon" />
            </div>
            <div className="ai-content">
                <h3>
                    AI Study Summary
                    <span className="beta-badge">Beta</span>
                </h3>
                <p>
                    You're trending <span className="highlight-positive">{positiveTrend} higher</span> in {subject} compared to last week. {recommendation}
                </p>
            </div>
            <button className="btn btn-secondary view-details-btn">
                View Details
            </button>
        </div>
    );
};

export default AISummary;
