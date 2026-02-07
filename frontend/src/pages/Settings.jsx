import { User, Mail, Phone, MapPin, Camera } from 'lucide-react';
import Header from '../components/Header';
import './Settings.css';

const Profile = () => {
    return (
        <div className="settings-page">
            <Header title="Profile" subtitle="Manage your personal information" />

            <div className="profile-container">
                <div className="profile-card glass-card">
                    <div className="profile-header">
                        <div className="profile-avatar-large">
                            <User size={48} />
                            <button className="avatar-edit-btn">
                                <Camera size={16} />
                            </button>
                        </div>
                        <div className="profile-header-info">
                            <h2>Student Account</h2>
                            <p>student@university.edu</p>
                        </div>
                    </div>

                    <div className="profile-form">
                        <div className="form-group">
                            <label><User size={16} /> Full Name</label>
                            <input type="text" placeholder="Enter your name" defaultValue="Student Account" />
                        </div>
                        <div className="form-group">
                            <label><Mail size={16} /> Email Address</label>
                            <input type="email" placeholder="Enter your email" defaultValue="student@university.edu" />
                        </div>
                        <div className="form-group">
                            <label><Phone size={16} /> Phone Number</label>
                            <input type="tel" placeholder="Enter your phone number" />
                        </div>
                        <div className="form-group">
                            <label><MapPin size={16} /> Location</label>
                            <input type="text" placeholder="Enter your location" />
                        </div>
                        <button className="save-profile-btn">Save Changes</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
