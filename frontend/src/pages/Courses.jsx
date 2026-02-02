import { useState, useEffect } from 'react';
import { Search, Filter, Bell, Settings } from 'lucide-react';
import Header from '../components/Header';
import './Courses.css';

const BASE_URL = 'http://localhost:8000';
const HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': 'default-secret-key',
};

const categories = ['All Courses', 'Computer Science', 'Arts & Design', 'Sciences', 'Humanities'];

const Courses = () => {
    const [activeCategory, setActiveCategory] = useState('All Courses');
    const [searchQuery, setSearchQuery] = useState('');
    const [enrolledCourses, setEnrolledCourses] = useState([]);
    const [catalogueCourses, setCatalogueCourses] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [catalogueRes, enrolledRes] = await Promise.all([
                fetch(`${BASE_URL}/courses`, { headers: HEADERS }),
                fetch(`${BASE_URL}/enrolled-courses`, { headers: HEADERS })
            ]);

            if (!catalogueRes.ok || !enrolledRes.ok) throw new Error('Failed to fetch courses');

            const catalogueData = await catalogueRes.json();
            const enrolledData = await enrolledRes.json();

            // Match categories and images for the UI
            const courseImages = [
                'https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=400&q=80',
                'https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=400&q=80',
                'https://images.unsplash.com/photo-1455390582262-044cdead277a?w=400&q=80',
                'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=400&q=80',
            ];

            const catalogue = catalogueData.courses.map((c, i) => ({
                ...c,
                image: courseImages[i % courseImages.length],
                category: c.code.startsWith('CS') ? 'Computer Science' :
                    c.code.startsWith('EE') ? 'Sciences' : 'Humanities', // Approximation
                semester: 'SPRING 2025'
            }));

            const enrolled = enrolledData.courses.map((c, i) => ({
                ...c,
                image: courseImages[(i + 2) % courseImages.length],
                progress: Math.floor(Math.random() * 100)
            }));

            setCatalogueCourses(catalogue);
            setEnrolledCourses(enrolled);
        } catch (error) {
            console.error('Error loading courses:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEnroll = async (course) => {
        try {
            const response = await fetch(`${BASE_URL}/enroll`, {
                method: 'POST',
                headers: HEADERS,
                body: JSON.stringify({
                    course_id: course.id,
                    course_name: course.name,
                    course_code: course.code,
                    credits: course.credits
                })
            });

            if (!response.ok) throw new Error('Enrollment failed');
            fetchData();
        } catch (error) {
            alert('Error enrolling: ' + error.message);
        }
    };

    const handleUnenroll = async (courseId) => {
        if (!window.confirm('Are you sure you want to drop this course?')) return;
        try {
            const response = await fetch(`${BASE_URL}/unenroll/${courseId}`, {
                method: 'DELETE',
                headers: HEADERS
            });

            if (!response.ok) throw new Error('Failed to drop course');
            fetchData();
        } catch (error) {
            alert('Error dropping course: ' + error.message);
        }
    };

    const filteredCourses = catalogueCourses.filter(course => {
        const matchesCategory = activeCategory === 'All Courses' || course.category === activeCategory;
        const matchesSearch = course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            course.code.toLowerCase().includes(searchQuery.toLowerCase());
        const isAlreadyEnrolled = enrolledCourses.some(e => e.code === course.code);
        return matchesCategory && matchesSearch && !isAlreadyEnrolled;
    });

    return (
        <div className="courses-page">
            <div className="courses-header">
                <div className="breadcrumb">
                    <span>Academics</span>
                    <span className="separator">›</span>
                    <span className="current">Courses</span>
                </div>
                <div className="header-actions">
                    <button className="icon-btn">
                        <Bell size={20} />
                    </button>
                    <button className="icon-btn">
                        <Settings size={20} />
                    </button>
                    <div className="user-avatar">
                        <span>👤</span>
                    </div>
                </div>
            </div>

            <h1 className="page-title">Courses & Catalogue</h1>
            <p className="page-description">
                Manage your current enrollment and discover new learning opportunities from our extensive course list.
            </p>

            {/* Enrolled Courses */}
            <section className="enrolled-section">
                <div className="section-header">
                    <h2>My Enrolled Courses</h2>
                    <a href="#" className="view-schedule-link">View Schedule</a>
                </div>

                <div className="enrolled-grid">
                    {enrolledCourses.map((course) => (
                        <div key={course.id} className="course-card enrolled">
                            <div
                                className="course-image"
                                style={{ backgroundImage: `url(${course.image})` }}
                            >
                                <span className="course-badge">{course.code}</span>
                            </div>
                            <div className="course-info">
                                <h3>{course.name}</h3>
                                <div className="progress-row">
                                    <span className="progress-label">Progress</span>
                                    <span className="progress-value">{course.progress}%</span>
                                </div>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${course.progress}%` }}
                                    />
                                </div>
                                <button
                                    className="continue-btn"
                                    onClick={() => handleUnenroll(course.id)}
                                    style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', marginTop: '0.5rem' }}
                                >
                                    Drop Course
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Course Catalogue */}
            <section className="catalogue-section">
                <div className="section-header">
                    <div>
                        <h2>Course Catalogue</h2>
                        <p>Browse available courses for the upcoming semester.</p>
                    </div>
                    <div className="catalogue-controls">
                        <div className="search-box">
                            <Search size={18} />
                            <input
                                type="text"
                                placeholder="Search courses..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                        <button className="filter-btn">
                            <Filter size={16} />
                            <span>Filter</span>
                        </button>
                    </div>
                </div>

                <div className="category-tabs">
                    {categories.map((category) => (
                        <button
                            key={category}
                            className={`category-tab ${activeCategory === category ? 'active' : ''}`}
                            onClick={() => setActiveCategory(category)}
                        >
                            {category}
                        </button>
                    ))}
                </div>

                <div className="catalogue-grid">
                    {filteredCourses.map((course) => (
                        <div key={course.id} className="course-card catalogue">
                            <div
                                className="course-image"
                                style={{ backgroundImage: `url(${course.image})` }}
                            >
                                <div className="course-tags">
                                    <span className="course-code-badge">{course.code}</span>
                                    <span className="semester-badge">{course.semester}</span>
                                </div>
                            </div>
                            <div className="course-info">
                                <h3>{course.name}</h3>
                                <span className="category-label">{course.category}</span>
                                <button
                                    className="enroll-btn"
                                    onClick={() => handleEnroll(course)}
                                >
                                    Enroll Now
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
};

export default Courses;
