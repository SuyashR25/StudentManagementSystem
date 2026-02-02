import { useState } from 'react';
import { History, Save, Plus, Sparkles, AlertTriangle, MoreVertical } from 'lucide-react';
import Header from '../components/Header';
import './Grades.css';


const gradeOptions = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F'];

const Grades = () => {
    const [courses, setCourses] = useState([]);
    const [targetCGPA, setTargetCGPA] = useState('0.00');

    const updateTargetGrade = (id, grade) => {
        setCourses(courses.map(course =>
            course.id === id ? { ...course, targetGrade: grade } : course
        ));
    };

    return (
        <div className="grades-page">
            <Header title="CGPA Calculator" subtitle="Simulate your future GPA with AI-powered predictions based on your performance history." />

            <div className="grades-actions">
                <button className="btn btn-secondary">
                    <History size={16} />
                    <span>History</span>
                </button>
                <button className="btn btn-primary">
                    <Save size={16} />
                    <span>Save Plan</span>
                </button>
            </div>

            <div className="grades-layout">
                <div className="grades-sidebar">
                    <div className="gpa-cards">
                        <div className="gpa-card current-gpa">
                            <span className="gpa-label">CURRENT CGPA</span>
                            <div className="gpa-value-row">
                                <span className="gpa-value">0.00</span>
                                <span className="gpa-change">--</span>
                            </div>
                            <span className="gpa-note">No data available</span>
                        </div>

                        <div className="gpa-card credits-card">
                            <span className="gpa-label">CREDITS EARNED</span>
                            <div className="gpa-value-row">
                                <span className="gpa-value">0</span>
                                <span className="gpa-divider">/ 120</span>
                            </div>
                            <div className="credits-bar">
                                <div className="credits-fill" style={{ width: '0%' }}></div>
                            </div>
                        </div>

                        <div className="gpa-card projected-card">
                            <span className="projected-label">PROJECTED CGPA</span>
                            <div className="projected-value">
                                <span className="big-value">--</span>
                                <span className="target-badge">Target</span>
                            </div>
                            <span className="projected-note">Set a goal to see projection</span>
                        </div>
                    </div>

                    <div className="goal-section glass-card">
                        <h3>Graduation Goal</h3>
                        <p>Enter your target cumulative GPA to calculate the grades needed.</p>

                        <div className="target-input-group">
                            <span className="input-icon">🎯</span>
                            <span className="input-label">Target CGPA</span>
                            <input
                                type="text"
                                value={targetCGPA}
                                onChange={(e) => setTargetCGPA(e.target.value)}
                                className="target-input"
                            />
                        </div>

                        <button className="ai-predict-btn">
                            <Sparkles size={16} />
                            <span>AI Grade Predictor</span>
                        </button>

                        <div className="ai-insight">
                            <div className="insight-header">
                                <Sparkles size={14} />
                                <span>AI Insight</span>
                            </div>
                            <p>
                                Set a target to receive AI insights.
                            </p>
                        </div>
                    </div>

                    <div className="semester-countdown">
                        <span className="countdown-label">Semester ends in</span>
                        <span className="countdown-value">-- Days</span>
                    </div>

                    <div className="challenge-warning glass-card">
                        <div className="warning-header">
                            <AlertTriangle size={16} />
                            <span>Challenging Goal</span>
                        </div>
                        <p>
                            This target is 0.2 higher than your average trend. Consider using Focus Tools for difficult subjects.
                        </p>
                    </div>
                </div>

                <div className="grades-main">
                    <div className="semester-header">
                        <h3>Current Semester</h3>
                        <button className="add-course-btn">
                            <Plus size={14} />
                            <span>Add Course</span>
                        </button>
                    </div>

                    <div className="courses-table glass-card">
                        <div className="table-header">
                            <span>COURSE</span>
                            <span>CREDITS</span>
                            <span>CURRENT GRADE</span>
                            <span>TARGET GRADE</span>
                            <span>ACTIONS</span>
                        </div>

                        {courses.map((course) => (
                            <div key={course.id} className="table-row">
                                <div className="course-info">
                                    <span className="course-code">{course.code}</span>
                                    <span className="course-name">{course.name}</span>
                                </div>
                                <span className="credits">{course.credits}</span>
                                <span className={`grade-badge current ${course.status}`}>
                                    {course.currentGrade}
                                </span>
                                <select
                                    className={`grade-select ${course.status}`}
                                    value={course.targetGrade}
                                    onChange={(e) => updateTargetGrade(course.id, e.target.value)}
                                >
                                    {gradeOptions.map((grade) => (
                                        <option key={grade} value={grade}>{grade}</option>
                                    ))}
                                </select>
                                <button className="more-btn">
                                    <MoreVertical size={16} />
                                </button>
                            </div>
                        ))}
                    </div>

                    <div className="table-footer">
                        <span className="showing-text">Showing {courses.length} courses</span>
                        <div className="status-legend">
                            <span className="legend-item">
                                <span className="dot achieved"></span>
                                Achieved
                            </span>
                            <span className="legend-item">
                                <span className="dot suggestion"></span>
                                AI Suggestion
                            </span>
                            <span className="legend-item">
                                <span className="dot risk"></span>
                                Risk
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Grades;
