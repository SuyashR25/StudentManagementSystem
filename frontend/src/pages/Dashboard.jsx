import Header from '../components/Header';
import AISummary from '../components/AISummary';
import { CGPACard, DegreeProgressCard, NextClassCard } from '../components/StatsCards';
import StudyActivityChart from '../components/StudyActivityChart';
import TodoList from '../components/TodoList';
import './Dashboard.css';

const Dashboard = () => {
    return (
        <div className="dashboard-page">
            <Header title="Dashboard Overview" />

            <AISummary />

            <div className="stats-grid">
                <CGPACard />
                <DegreeProgressCard />
                <NextClassCard />
            </div>

            <div className="bottom-grid">
                <StudyActivityChart />
                <TodoList />
            </div>
        </div>
    );
};

export default Dashboard;
