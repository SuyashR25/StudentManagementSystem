import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Send, Paperclip, MessageSquare, Plus, Loader2, ChevronLeft } from 'lucide-react';
import './AiChat.css';

const BASE_URL = 'http://localhost:8000';
const HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': 'default-secret-key',
};

const AiChat = ({ isOpen, onClose }) => {
    const [threads, setThreads] = useState([]);
    const [activeThreadId, setActiveThreadId] = useState('default');
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isFetchingThreads, setIsFetchingThreads] = useState(false);
    const [attachedFiles, setAttachedFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);
    const [currentView, setCurrentView] = useState('threads'); // 'threads' or 'chat'

    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    const scrollToBottom = useCallback(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, []);

    const fetchThreads = useCallback(async () => {
        setIsFetchingThreads(true);
        try {
            const response = await fetch(`${BASE_URL}/chat/threads?user_id=1`, { headers: HEADERS });
            if (!response.ok) throw new Error('Fetch threads failed');
            const data = await response.json();
            setThreads(data.threads || []);
        } catch (error) {
            console.error('Error fetching threads:', error);
        } finally {
            setIsFetchingThreads(false);
        }
    }, []);

    const fetchMessages = useCallback(async (threadId) => {
        if (!threadId) return;
        setIsLoading(true);
        try {
            const response = await fetch(`${BASE_URL}/chat/history?user_id=1&thread_id=${threadId}&limit=50`, { headers: HEADERS });
            if (!response.ok) throw new Error('Fetch messages failed');
            const data = await response.json();
            setMessages(data.messages || []);
        } catch (error) {
            console.error('Error fetching messages:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Initial load when opened
    useEffect(() => {
        if (isOpen) {
            fetchThreads();
            fetchMessages(activeThreadId);
        }
    }, [isOpen, fetchThreads, fetchMessages, activeThreadId]);

    // Scroll to bottom on new messages
    useEffect(() => {
        if (currentView === 'chat') {
            scrollToBottom();
        }
    }, [messages, currentView, scrollToBottom]);

    const handleSelectThread = (threadId) => {
        setActiveThreadId(threadId);
        setCurrentView('chat');
        fetchMessages(threadId);
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() && attachedFiles.length === 0) return;

        const currentInput = input;
        const currentFiles = [...attachedFiles];
        const currentThreadId = activeThreadId;

        setInput('');
        setAttachedFiles([]);

        const tempUserMessage = { role: 'user', message: currentInput, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, tempUserMessage]);

        setIsLoading(true);
        try {
            let filePaths = [];
            if (currentFiles.length > 0) {
                setIsUploading(true);
                for (const file of currentFiles) {
                    const formData = new FormData();
                    formData.append('file', file);
                    const uploadRes = await fetch(`${BASE_URL}/upload`, {
                        method: 'POST',
                        headers: { 'X-API-Key': 'default-secret-key' },
                        body: formData
                    });
                    const uploadData = await uploadRes.json();
                    if (uploadData.path) filePaths.push(uploadData.path);
                }
                setIsUploading(false);
            }

            const response = await fetch(`${BASE_URL}/query`, {
                method: 'POST',
                headers: HEADERS,
                body: JSON.stringify({
                    query: currentInput,
                    file_paths: filePaths,
                    thread_id: currentThreadId,
                    user_id: "1"
                })
            });

            if (!response.ok) throw new Error('Query failed');

            // Handle Streaming
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = { role: 'assistant', message: '', timestamp: new Date().toISOString() };

            setMessages(prev => [...prev, assistantMessage]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'token') {
                                assistantMessage.message += data.content;
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = { ...assistantMessage };
                                    return newMessages;
                                });
                            } else if (data.type === 'final') {
                                // Final summary/response update if needed
                                assistantMessage.message = data.response || assistantMessage.message;
                                setMessages(prev => {
                                    const newMessages = [...prev];
                                    newMessages[newMessages.length - 1] = { ...assistantMessage };
                                    return newMessages;
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing stream chunk:', e);
                        }
                    }
                }
            }

            fetchThreads(); // Sub-count might have changed
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files);
        const validFiles = files.filter(file => {
            const ext = file.name.split('.').pop().toLowerCase();
            return ['pdf', 'ppt', 'pptx'].includes(ext);
        });
        if (validFiles.length !== files.length) {
            alert('Only PDF and PPTX files are supported.');
        }
        setAttachedFiles(prev => [...prev, ...validFiles]);
    };

    const handleDeleteThread = async (e, threadId) => {
        e.stopPropagation();
        if (!window.confirm(`Delete thread ${threadId}?`)) return;

        try {
            const response = await fetch(`${BASE_URL}/chat/threads/${threadId}?user_id=1`, {
                method: 'DELETE',
                headers: { 'X-API-Key': 'default-secret-key' }
            });
            if (!response.ok) throw new Error('Delete failed');
            fetchThreads();
            if (activeThreadId === threadId) {
                setActiveThreadId('default');
                setMessages([]);
                setCurrentView('threads');
            }
        } catch (error) {
            console.error('Error deleting thread:', error);
        }
    };

    const createNewThread = () => {
        const newId = `thread_${Date.now()}`;
        setActiveThreadId(newId);
        setMessages([]);
        setCurrentView('chat');
    };

    if (!isOpen) return null;

    return (
        <div className="ai-chat-overlay" onClick={onClose}>
            <div className="ai-chat-container" onClick={e => e.stopPropagation()}>
                {currentView === 'threads' ? (
                    <div className="ai-chat-view threads-view">
                        <div className="view-header">
                            <div className="bot-info">
                                <div className="bot-avatar">🤖</div>
                                <h3>AI Assistant</h3>
                            </div>
                            <button className="close-btn" onClick={onClose}><X size={20} /></button>
                        </div>
                        <div className="view-body">
                            <button className="create-new-btn" onClick={createNewThread}>
                                <Plus size={18} /><span>New Conversation</span>
                            </button>
                            <div className="thread-list">
                                <h4 className="list-label">History</h4>
                                <div className={`thread-item ${activeThreadId === 'default' ? 'active' : ''}`} onClick={() => handleSelectThread('default')}>
                                    <MessageSquare size={18} /><div className="thread-info"><span className="thread-id">Default Thread</span><span className="thread-meta">General</span></div>
                                </div>
                                {isFetchingThreads ? <div className="loader-container"><Loader2 className="animate-spin" /></div> :
                                    threads.map(t => (
                                        <div key={t.thread_id} className={`thread-item ${activeThreadId === t.thread_id ? 'active' : ''}`} onClick={() => handleSelectThread(t.thread_id)}>
                                            <MessageSquare size={18} /><div className="thread-info"><span className="thread-id">{t.thread_id}</span><span className="thread-meta">{t.message_count} messages</span></div>
                                            <button className="delete-thread-btn" onClick={(e) => handleDeleteThread(e, t.thread_id)}><X size={14} /></button>
                                        </div>
                                    ))
                                }
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="ai-chat-view chat-view">
                        <div className="view-header">
                            <button className="back-btn" onClick={() => setCurrentView('threads')}><ChevronLeft size={24} /></button>
                            <div className="bot-info"><h4>Agentic Assistant</h4><p className="status">{activeThreadId}</p></div>
                            <button className="close-btn" onClick={onClose}><X size={20} /></button>
                        </div>
                        <div className="messages-container">
                            {messages.length === 0 && !isLoading && (
                                <div className="empty-state"><div className="bot-avatar large">🤖</div><h3>Empty chat</h3><p>Ask anything!</p></div>
                            )}
                            {messages.map((msg, i) => (
                                <div key={i} className={`message-wrapper ${msg.role}`}>
                                    <div className="message-content"><p>{msg.message}</p>
                                        <span className="timestamp">{msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                                    </div>
                                </div>
                            ))}
                            {isLoading && <div className="message-wrapper assistant"><div className="message-content loading"><Loader2 className="animate-spin" size={16} /><span>Thinking...</span></div></div>}
                            <div ref={messagesEndRef} />
                        </div>
                        <form className="chat-input-area" onSubmit={handleSendMessage}>
                            {attachedFiles.length > 0 && (
                                <div className="attached-files-preview">
                                    {attachedFiles.map((f, i) => (
                                        <div key={i} className="file-chip"><span>{f.name}</span><button type="button" onClick={() => setAttachedFiles(prev => prev.filter((_, idx) => idx !== i))}><X size={12} /></button></div>
                                    ))}
                                </div>
                            )}
                            <div className="input-row">
                                <button type="button" className="action-btn" onClick={() => fileInputRef.current?.click()}><Paperclip size={20} /></button>
                                <input type="file" ref={fileInputRef} style={{ display: 'none' }} multiple accept=".pdf,.ppt,.pptx" onChange={handleFileChange} />
                                <input type="text" placeholder="Type a message..." value={input} onChange={e => setInput(e.target.value)} disabled={isLoading} />
                                <button type="submit" className="send-btn" disabled={(!input.trim() && attachedFiles.length === 0) || isLoading}><Send size={20} /></button>
                            </div>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
};
export default AiChat;
