import { NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    BookOpen,
    Calendar,
    GraduationCap,
    Timer,
    Settings,
    User
} from 'lucide-react';
import './Sidebar.css';

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard', filled: true },
    { path: '/courses', icon: BookOpen, label: 'Courses' },
    { path: '/calendar', icon: Calendar, label: 'Calendar' },
    { path: '/grades', icon: GraduationCap, label: 'Grades' },
    { path: '/focus', icon: Timer, label: 'Focus Timer' },
    { path: '/settings', icon: User, label: 'Profile' },
];

const Sidebar = () => {
    const location = useLocation();

    return (
        <aside className="sidebar glass-sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="logo-icon">
                    <GraduationCap size={24} />
                </div>
                <div className="logo-text">
                    <h1>EduTrack</h1>
                    <p>Student Portal</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={`nav-item ${isActive ? 'active' : ''}`}
                        >
                            <Icon
                                size={20}
                                fill={isActive ? 'currentColor' : 'none'}
                                strokeWidth={isActive ? 1.5 : 2}
                            />
                            <span>{item.label}</span>
                        </NavLink>
                    );
                })}
            </nav>

            {/* User Profile */}
            <div className="sidebar-profile">
                <div className="profile-avatar">
                    <User size={20} />
                </div>
                <div className="profile-info">
                    <p className="profile-name">Student Account</p>
                    <p className="profile-role">Academic Portal</p>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
