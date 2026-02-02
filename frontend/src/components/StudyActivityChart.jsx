import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import './StudyActivityChart.css';


const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="chart-tooltip">
                <p className="tooltip-label">{label}</p>
                <p className="tooltip-value">{payload[0].value}h studied</p>
            </div>
        );
    }
    return null;
};

const StudyActivityChart = ({ data = [] }) => {
    return (
        <div className="chart-card glass-card">
            <div className="chart-header">
                <div>
                    <h3 className="chart-title">Study Activity</h3>
                    <p className="chart-subtitle">Weekly hours spent focusing</p>
                </div>
                <select className="chart-select">
                    <option value="this-week">This Week</option>
                    <option value="last-week">Last Week</option>
                    <option value="this-month">This Month</option>
                </select>
            </div>

            <div className="chart-container">
                <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={data} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.4} />
                                <stop offset="100%" stopColor="var(--primary)" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <XAxis
                            dataKey="day"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
                            tickFormatter={(value) => `${value}h`}
                            width={35}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                            type="monotone"
                            dataKey="hours"
                            stroke="var(--primary)"
                            strokeWidth={3}
                            fill="url(#colorHours)"
                            dot={{ fill: 'white', stroke: 'var(--primary)', strokeWidth: 2, r: 4 }}
                            activeDot={{ fill: 'white', stroke: 'var(--primary)', strokeWidth: 3, r: 6 }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default StudyActivityChart;
