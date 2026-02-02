import { User, Bell, Shield, Palette, Globe, HelpCircle } from 'lucide-react';
import Header from '../components/Header';
import './Settings.css';

const settingsSections = [
    {
        id: 'profile',
        icon: User,
        title: 'Profile Settings',
        description: 'Update your personal information and profile picture',
    },
    {
        id: 'notifications',
        icon: Bell,
        title: 'Notifications',
        description: 'Manage email and push notification preferences',
    },
    {
        id: 'privacy',
        icon: Shield,
        title: 'Privacy & Security',
        description: 'Control your data and account security settings',
    },
    {
        id: 'appearance',
        icon: Palette,
        title: 'Appearance',
        description: 'Customize theme, colors, and display options',
    },
    {
        id: 'language',
        icon: Globe,
        title: 'Language & Region',
        description: 'Set your preferred language and timezone',
    },
    {
        id: 'help',
        icon: HelpCircle,
        title: 'Help & Support',
        description: 'Get help, report issues, or contact support',
    },
];

const Settings = () => {
    return (
        <div className="settings-page">
            <Header title="Settings" subtitle="Manage your account and preferences" />

            <div className="settings-grid">
                {settingsSections.map((section) => {
                    const Icon = section.icon;
                    return (
                        <div key={section.id} className="settings-card glass-card">
                            <div className="settings-icon">
                                <Icon size={24} />
                            </div>
                            <div className="settings-content">
                                <h3>{section.title}</h3>
                                <p>{section.description}</p>
                            </div>
                            <span className="arrow">→</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default Settings;
