import { useState, useEffect, useCallback } from 'react';
import { Plus, PlusCircle, Loader2, Trash2, X } from 'lucide-react';
import './TodoList.css';

const BASE_URL = 'http://localhost:8000';
const HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': 'default-secret-key',
};

const TodoList = () => {
    const [todos, setTodos] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isAdding, setIsAdding] = useState(false);
    const [newTodoText, setNewTodoText] = useState('');
    const [newTodoPriority, setNewTodoPriority] = useState('Medium');

    const fetchTodos = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${BASE_URL}/todos?user_id=1`, { headers: HEADERS });
            if (!response.ok) throw new Error('Fetch failed');
            const data = await response.json();
            setTodos(data.todos || []);
        } catch (error) {
            console.error('Error fetching todos:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTodos();
    }, [fetchTodos]);

    const handleAddTodo = async (e) => {
        e.preventDefault();
        if (!newTodoText.trim()) return;

        try {
            const response = await fetch(`${BASE_URL}/todos`, {
                method: 'POST',
                headers: HEADERS,
                body: JSON.stringify({
                    user_id: "1",
                    text: newTodoText,
                    priority: newTodoPriority,
                    tag: "General"
                })
            });
            if (!response.ok) throw new Error('Add failed');
            setNewTodoText('');
            setIsAdding(false);
            setNewTodoPriority('Medium');
            fetchTodos();
        } catch (error) {
            console.error('Error adding todo:', error);
        }
    };

    const toggleTodo = async (id, completed) => {
        try {
            const response = await fetch(`${BASE_URL}/todos/${id}`, {
                method: 'PATCH',
                headers: HEADERS,
                body: JSON.stringify({ completed: !completed })
            });
            if (!response.ok) throw new Error('Toggle failed');
            fetchTodos();
        } catch (error) {
            console.error('Error toggling todo:', error);
        }
    };

    const deleteTodo = async (id) => {
        try {
            const response = await fetch(`${BASE_URL}/todos/${id}`, {
                method: 'DELETE',
                headers: HEADERS
            });
            if (!response.ok) throw new Error('Delete failed');
            fetchTodos();
        } catch (error) {
            console.error('Error deleting todo:', error);
        }
    };

    const clearAll = async () => {
        if (!window.confirm('Clear all tasks?')) return;
        try {
            const response = await fetch(`${BASE_URL}/todos?user_id=1`, {
                method: 'DELETE',
                headers: HEADERS
            });
            if (!response.ok) throw new Error('Clear failed');
            fetchTodos();
        } catch (error) {
            console.error('Error clearing todos:', error);
        }
    };

    return (
        <div className="todo-card glass-card">
            <div className="todo-header">
                <div className="header-left">
                    <h3 className="todo-title">To-Do List</h3>
                    <span className="todo-count">{todos.filter(t => !t.completed).length} pending</span>
                </div>
                <div className="header-actions">
                    <button className="icon-btn clear-btn" onClick={clearAll} title="Clear All">
                        <Trash2 size={16} />
                    </button>
                </div>
            </div>

            <div className="todo-list">
                {isAdding && (
                    <form className="add-todo-inline" onSubmit={handleAddTodo}>
                        <div className="inline-input-row">
                            <input
                                autoFocus
                                type="text"
                                placeholder="What needs to be done?"
                                value={newTodoText}
                                onChange={(e) => setNewTodoText(e.target.value)}
                            />
                            <div className="inline-actions">
                                <button type="submit" className="inline-add"><Plus size={14} /></button>
                                <button type="button" className="inline-cancel" onClick={() => { setIsAdding(false); setNewTodoText(''); }}><X size={14} /></button>
                            </div>
                        </div>
                        <div className="priority-selector">
                            <span className="priority-label">Difficulty:</span>
                            {['Low', 'Medium', 'High'].map((p) => (
                                <button
                                    key={p}
                                    type="button"
                                    className={`priority-btn ${p.toLowerCase()} ${newTodoPriority === p ? 'active' : ''}`}
                                    onClick={() => setNewTodoPriority(p)}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    </form>
                )}

                {isLoading && todos.length === 0 ? (
                    <div className="todo-loading"><Loader2 className="animate-spin" /></div>
                ) : todos.length === 0 && !isAdding ? (
                    <div className="todo-empty">No tasks yet. Add one below!</div>
                ) : (
                    todos.map((todo) => (
                        <div key={todo.id} className={`todo-item-container ${todo.completed ? 'completed' : ''}`}>
                            <label className="todo-item">
                                <input
                                    type="checkbox"
                                    className="custom-checkbox"
                                    checked={!!todo.completed}
                                    onChange={() => toggleTodo(todo.id, !!todo.completed)}
                                />
                                <div className="todo-content">
                                    <span className="todo-text">{todo.text}</span>
                                    {(todo.due_date || todo.priority) && (
                                        <div className="todo-meta">
                                            {todo.due_date && <span className="todo-due">{todo.due_date}</span>}
                                            {todo.priority && <span className={`todo-priority ${todo.priority.toLowerCase()}`}>{todo.tag} • {todo.priority}</span>}
                                        </div>
                                    )}
                                </div>
                            </label>
                            <button className="delete-item-btn" onClick={() => deleteTodo(todo.id)}>
                                <X size={14} />
                            </button>
                        </div>
                    ))
                )}
            </div>

            {!isAdding && (
                <div className="todo-footer">
                    <button className="add-task-btn" onClick={() => setIsAdding(true)}>
                        <PlusCircle size={16} />
                        <span>Add new task</span>
                    </button>
                </div>
            )}
        </div>
    );
};

export default TodoList;
