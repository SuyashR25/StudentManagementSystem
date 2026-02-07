import { useState, useEffect } from 'react';
import { Save, Sparkles, BookOpen } from 'lucide-react';
import Header from '../components/Header';
import './Grades.css';

const API_BASE = 'http://localhost:8000';
const gradeOptions = ['AA', 'AB', 'BB', 'BC', 'CC', 'FR'];

const Grades = () => {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [targetCGPA, setTargetCGPA] = useState('8.50');

    useEffect(() => {
        fetchEnrolledCourses();
    }, []);

    const fetchEnrolledCourses = async () => {
        try {
            const response = await fetch(`${API_BASE}/enrolled-courses`, {
                headers: {
                    'X-API-Key': 'default-secret-key'
                }
            });
            if (response.ok) {
                const data = await response.json();
                // API returns {courses: [...], count: N}
                const coursesArray = data.courses || [];
                // Add target grade field to each course
                const coursesWithTargets = coursesArray.map(course => ({
                    ...course,
                    targetGrade: course.grade || 'AA'
                }));
                setCourses(coursesWithTargets);
            }
        } catch (error) {
            console.error('Error fetching enrolled courses:', error);
        } finally {
            setLoading(false);
        }
    };

    const updateTargetGrade = (id, grade) => {
        setCourses(courses.map(course =>
            course.id === id ? { ...course, targetGrade: grade } : course
        ));
    };

    const calculateProjectedGPA = () => {
        if (courses.length === 0) return '--';
        const gradePoints = {
            'AA': 10, 'AB': 9, 'BB': 8, 'BC': 7, 'CC': 6, 'FR': 0
        };
        let totalPoints = 0;
        let totalCredits = 0;
        courses.forEach(course => {
            const points = gradePoints[course.targetGrade] || 0;
            const credits = course.credits || 3;
            totalPoints += points * credits;
            totalCredits += credits;
        });
        return totalCredits > 0 ? (totalPoints / totalCredits).toFixed(2) : '--';
    };

    const totalCredits = courses.reduce((sum, c) => sum + (c.credits || 3), 0);

    return (
        <div className="grades-page">
            <Header title="Grades & Target Planning" subtitle="Set target grades for your enrolled courses this semester" />

            <div className="grades-layout">
                <div className="grades-sidebar">
                    <div className="gpa-cards">
                        <div className="gpa-card projected-card">
                            <span className="projected-label">PROJECTED GPA</span>
                            <div className="projected-value">
                                <span className="big-value">{calculateProjectedGPA()}</span>
                                <span className="gpa-scale">/ 10</span>
                            </div>
                            <span className="projected-note">Based on target grades</span>
                        </div>

                        <div className="gpa-card credits-card">
                            <span className="gpa-label">SEMESTER CREDITS</span>
                            <div className="gpa-value-row">
                                <span className="gpa-value">{totalCredits}</span>
                            </div>
                            <span className="gpa-note">{courses.length} courses enrolled</span>
                        </div>
                    </div>

                    <div className="goal-section glass-card">
                        <h3>🎯 Graduation Goal</h3>
                        <p>Enter your target cumulative GPA</p>
                        <div className="target-input-group">
                            <input
                                type="text"
                                value={targetCGPA}
                                onChange={(e) => setTargetCGPA(e.target.value)}
                                className="target-input"
                                placeholder="8.50"
                            />
                            <span className="gpa-scale-input">/ 10</span>
                        </div>
                        <button className="ai-predict-btn">
                            <Sparkles size={16} />
                            <span>AI Grade Predictor</span>
                        </button>
                    </div>
                </div>

                <div className="grades-main">
                    <div className="semester-header">
                        <h3><BookOpen size={20} /> Current Semester Courses</h3>
                        <button className="btn btn-primary save-btn">
                            <Save size={16} />
                            <span>Save Targets</span>
                        </button>
                    </div>

                    <div className="courses-table glass-card">
                        <div className="table-header">
                            <span>COURSE</span>
                            <span>CODE</span>
                            <span>CREDITS</span>
                            <span>TARGET GRADE</span>
                        </div>

                        {loading ? (
                            <div className="loading-state">Loading enrolled courses...</div>
                        ) : courses.length === 0 ? (
                            <div className="empty-state">
                                <BookOpen size={40} />
                                <p>No courses enrolled this semester</p>
                                <span>Use the AI chat to enroll in courses</span>
                            </div>
                        ) : (
                            courses.map((course) => (
                                <div key={course.id} className="table-row">
                                    <div className="course-info">
                                        <span className="course-name">{course.name}</span>
                                    </div>
                                    <span className="course-code">{course.code}</span>
                                    <span className="credits">{course.credits || 3}</span>
                                    <select
                                        className="grade-select"
                                        value={course.targetGrade}
                                        onChange={(e) => updateTargetGrade(course.id, e.target.value)}
                                    >
                                        {gradeOptions.map((grade) => (
                                            <option key={grade} value={grade}>{grade}</option>
                                        ))}
                                    </select>
                                </div>
                            ))
                        )}
                    </div>

                    <div className="table-footer">
                        <span className="showing-text">
                            {courses.length} enrolled course{courses.length !== 1 ? 's' : ''}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Grades;
