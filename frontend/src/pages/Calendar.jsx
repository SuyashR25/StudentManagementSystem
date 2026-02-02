import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Send, Sparkles, X, User, Plus } from 'lucide-react';
import Header from '../components/Header';
import './Calendar.css';

const daysOfWeek = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
const BASE_URL = 'http://localhost:8000';
const HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': 'default-secret-key',
};

const Calendar = () => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [newEvent, setNewEvent] = useState({
        title: '',
        category: 'academic',
        date: new Date().toISOString().split('T')[0],
        startTime: '09:00',
        endTime: '10:00',
        description: ''
    });

    const handleAddEvent = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            const startStr = `${newEvent.date}T${newEvent.startTime}:00`;
            const endStr = `${newEvent.date}T${newEvent.endTime}:00`;

            const response = await fetch(`${BASE_URL}/events`, {
                method: 'POST',
                headers: HEADERS,
                body: JSON.stringify({
                    title: newEvent.title,
                    start_datetime: startStr,
                    end_datetime: endStr,
                    category: newEvent.category,
                    priority: newEvent.priority || 'medium',
                    description: newEvent.description,
                    user_id: '1'
                }),
            });

            if (!response.ok) throw new Error('Failed to create event');

            setShowModal(false);
            setNewEvent({
                title: '',
                category: 'academic',
                date: new Date().toISOString().split('T')[0],
                startTime: '09:00',
                endTime: '10:00',
                description: ''
            });
            fetchEvents();
        } catch (error) {
            alert('Error adding event: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteEvent = async (eventId) => {
        if (!window.confirm('Are you sure you want to delete this event?')) return;

        setIsLoading(true);
        try {
            const response = await fetch(`${BASE_URL}/events/${eventId}`, {
                method: 'DELETE',
                headers: HEADERS
            });

            if (!response.ok) throw new Error('Failed to delete event');

            fetchEvents();
        } catch (error) {
            alert('Error deleting event: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchEvents();
    }, []); // Fetch once on mount

    const fetchEvents = async () => {
        try {
            const response = await fetch(`${BASE_URL}/events?limit=500`, { // Increase limit to get "all"
                headers: HEADERS
            });

            if (!response.ok) throw new Error('Failed to fetch events');
            const data = await response.json();

            // Map backend events to frontend format (just store raw events with a Date object)
            const formattedEvents = data.events.map(e => ({
                ...e,
                startDate: new Date(e.start_datetime),
                color: getColorForPriority(e.priority)
            }));
            setEvents(formattedEvents);
        } catch (error) {
            console.error('Failed to fetch events:', error);
        }
    };

    const getColorForPriority = (priority) => {
        const map = {
            low: 'green',
            medium: 'yellow',
            high: 'red',
        };
        return map[priority?.toLowerCase()] || 'blue';
    };

    const getDaysInMonth = (date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        let startDay = firstDay.getDay() - 1;
        if (startDay < 0) startDay = 6;

        const days = [];

        // Previous month days
        const prevMonth = new Date(year, month, 0);
        const prevMonthDays = prevMonth.getDate();
        for (let i = startDay - 1; i >= 0; i--) {
            days.push({ day: prevMonthDays - i, isCurrentMonth: false });
        }

        // Current month days
        for (let i = 1; i <= daysInMonth; i++) {
            const dayEvents = events.filter(e => {
                const d = e.startDate;
                return d.getFullYear() === year && d.getMonth() === month && d.getDate() === i;
            });
            days.push({ day: i, isCurrentMonth: true, events: dayEvents });
        }

        // Next month days
        const remainingDays = 42 - days.length;
        for (let i = 1; i <= remainingDays; i++) {
            days.push({ day: i, isCurrentMonth: false });
        }

        return days;
    };

    const days = getDaysInMonth(currentDate);


    const changeMonth = (offset) => {
        const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + offset, 1);
        setCurrentDate(newDate);
    };

    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    return (
        <div className="calendar-page">
            <Header title="Schedule" subtitle="Manage your academic deadlines with AI assistance." />

            <div className="calendar-content">
                <div className="calendar-main">
                    <div className="calendar-controls">
                        <div className="month-navigation">
                            <button className="nav-btn" onClick={() => changeMonth(-1)}>
                                <ChevronLeft size={18} />
                            </button>
                            <span className="current-month">
                                {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
                            </span>
                            <button className="nav-btn" onClick={() => changeMonth(1)}>
                                <ChevronRight size={18} />
                            </button>
                            <button className="today-btn" onClick={() => setCurrentDate(new Date())}>Today</button>
                            <button className="add-event-btn" onClick={() => setShowModal(true)}>
                                <Plus size={16} />
                                <span>Add Event</span>
                            </button>
                            <div className="ai-indicator">
                                <span className="ai-dot"></span>
                                <span>AI</span>
                            </div>
                        </div>
                    </div>

                    <div className="calendar-grid">
                        <div className="calendar-header">
                            {daysOfWeek.map((day) => (
                                <div key={day} className="day-header">{day}</div>
                            ))}
                        </div>

                        <div className="calendar-body">
                            {days.map((item, index) => (
                                <div
                                    key={index}
                                    className={`calendar-cell ${!item.isCurrentMonth ? 'other-month' : ''}`}
                                >
                                    <span className="day-number">{item.day}</span>
                                    <div className="cell-events">
                                        {item.events?.map((event) => (
                                            <div
                                                key={event.id}
                                                className={`event-pill ${event.color}`}
                                            >
                                                <span className="event-title">{event.title}</span>
                                                <button
                                                    className="delete-pill-btn"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteEvent(event.id);
                                                    }}
                                                >
                                                    <X size={10} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content glass-card">
                        <div className="modal-header">
                            <h3>Add New Event</h3>
                            <button className="close-btn" onClick={() => setShowModal(false)}>
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleAddEvent}>
                            <div className="form-group">
                                <label>Title</label>
                                <input
                                    type="text"
                                    required
                                    value={newEvent.title}
                                    onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                                    placeholder="Event title"
                                />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Category</label>
                                    <select
                                        value={newEvent.category}
                                        onChange={(e) => setNewEvent({ ...newEvent, category: e.target.value })}
                                    >
                                        <option value="academic">Academic</option>
                                        <option value="personal">Personal</option>
                                        <option value="work">Work</option>
                                        <option value="general">General</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Difficulty (Priority)</label>
                                    <select
                                        value={newEvent.priority || 'medium'}
                                        onChange={(e) => setNewEvent({ ...newEvent, priority: e.target.value })}
                                    >
                                        <option value="low">Low (Easy)</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High (Hard)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Date</label>
                                    <input
                                        type="date"
                                        required
                                        value={newEvent.date}
                                        onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Start Time</label>
                                    <input
                                        type="time"
                                        required
                                        value={newEvent.startTime}
                                        onChange={(e) => setNewEvent({ ...newEvent, startTime: e.target.value })}
                                    />
                                </div>
                                <div className="form-group">
                                    <label>End Time</label>
                                    <input
                                        type="time"
                                        required
                                        value={newEvent.endTime}
                                        onChange={(e) => setNewEvent({ ...newEvent, endTime: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <textarea
                                    value={newEvent.description}
                                    onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                                    placeholder="Event description (optional)"
                                />
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={isLoading}>
                                    {isLoading ? 'Creating...' : 'Create Event'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Calendar;
