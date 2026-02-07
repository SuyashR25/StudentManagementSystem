import { Menu } from 'lucide-react';
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

        </header>
    );
};

export default Header;
