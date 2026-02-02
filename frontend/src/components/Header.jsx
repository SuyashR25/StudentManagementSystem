import { Bell, Plus, Menu } from 'lucide-react';
import './Header.css';

const Header = ({ title, subtitle, onMenuClick }) => {
    const currentDate = new Date().toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
    });

    return (
        <header className="main-header">
            <div className="header-left">
                <button className="mobile-menu-btn" onClick={onMenuClick}>
                    <Menu size={24} />
                </button>
                <div className="header-info">
                    <h2>{title}</h2>
                    <p>
                        <span className="header-icon">📅</span>
                        {subtitle || `Fall Semester 2025 • ${currentDate}`}
                    </p>
                </div>
            </div>
            <div className="header-right">
                <button className="notification-btn glass-card">
                    <Bell size={20} />
                    <span className="notification-dot"></span>
                </button>
                <button className="btn btn-primary new-project-btn">
                    <Plus size={18} />
                    <span>New Project</span>
                </button>
            </div>
        </header>
    );
};

export default Header;
