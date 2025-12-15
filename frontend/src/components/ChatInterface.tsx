import React, { useState, useRef, useEffect } from 'react';
import { createSession, streamChat } from '../api/client';
import { Send, Bot, User, ThumbsUp, ThumbsDown } from 'lucide-react';

interface Message {
    id: string;
    role: 'user' | 'bot';
    content: string;
    timestamp: Date;
    generated?: boolean; // true for actual bot responses from the backend
}

interface ChatInterfaceProps {
    user: string;
}

const mergeStreamContent = (current: string, incoming: string): string => {
    if (!incoming) {
        return current;
    }

    if (!current) {
        return incoming;
    }

    let overlap = Math.min(current.length, incoming.length);
    while (overlap > 0 && !current.endsWith(incoming.slice(0, overlap))) {
        overlap -= 1;
    }

    const addition = incoming.slice(overlap);

    if (!addition.trim()) {
        return current;
    }

    const additionTrimStart = addition.trimStart();

    if (current.endsWith(addition) || (additionTrimStart && current.endsWith(additionTrimStart))) {
        return current;
    }

    const leading = incoming.slice(0, incoming.length - addition.length);
    if (leading === current && (addition === current || additionTrimStart === current)) {
        return current;
    }

    if (additionTrimStart && additionTrimStart.startsWith(current)) {
        return current;
    }

    return current + addition;
};

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ user }) => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'bot',
            content: `Hello ${user}! I am Funda Fargo. How can I help you today?`,
            timestamp: new Date(),
            generated: false,
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [feedback, setFeedback] = useState<Record<string, 'like' | 'dislike' | undefined>>({});

    useEffect(() => {
        const initSession = async () => {
            try {
                const newSessionId = await createSession(user);
                setSessionId(newSessionId);
            } catch (error) {
                console.error("Failed to create session", error);
            }
        };
        initSession();
    }, [user]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !sessionId) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        const botMessageId = `bot-${Date.now()}`;
        const botTimestamp = new Date();

        setMessages(prev => [
            ...prev,
            userMessage,
            {
                id: botMessageId,
                role: 'bot',
                content: '',
                timestamp: botTimestamp,
                generated: false,
            },
        ]);
        setInput('');
        setIsLoading(true);

        streamChat(
            sessionId,
            user,
            input,
            (delta) => {
                setMessages(prev => prev.map(msg =>
                    msg.id === botMessageId
                        ? {
                            ...msg,
                            content: mergeStreamContent(msg.content, delta),
                        }
                        : msg
                ));
            },
            (final) => {
                setIsLoading(false);
                setMessages(prev => prev.map(msg =>
                    msg.id === botMessageId
                        ? {
                            ...msg,
                            content: mergeStreamContent(msg.content, final || ''),
                            timestamp: new Date(),
                            generated: true,
                        }
                        : msg
                ));
                // Initialize empty feedback for this bot message
                setFeedback(prev => ({ ...prev, [botMessageId]: prev[botMessageId] }));
            },
            (error) => {
                console.error("Streaming error:", error);
                setMessages(prev => prev.map(msg =>
                    msg.id === botMessageId
                        ? {
                            ...msg,
                            content: "Sorry, I encountered an error. Please try again.",
                            timestamp: new Date(),
                        }
                        : msg
                ));
                setIsLoading(false);
            }
        );
    };

    return (
        <div className="chat-interface">
            {/* Header */}
            <header className="chat-header">
                <h1>Fargo Funda</h1>
                <p>Powered by Brainwave</p>
            </header>

            {/* Messages Area */}
            <div className="messages-area custom-scrollbar">
                <div className="messages-list">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`message-row ${msg.role === 'user' ? 'message-row-user' : ''}`}
                        >
                            <div className="avatar-stack">
                                <div className="avatar">
                                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                                </div>
                                <span className="timestamp">
                                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>

                            <div className="message-bubble">
                                {msg.content ? (
                                    <p>{msg.content}</p>
                                ) : (
                                    msg.role === 'bot' && isLoading ? (
                                        <div className="typing-indicator">
                                            <span></span>
                                            <span></span>
                                            <span></span>
                                        </div>
                                    ) : null
                                )}
                            </div>
                            {msg.role === 'bot' && msg.content && msg.generated && (
                                <div className="feedback-bar below">
                                    <button
                                        type="button"
                                        aria-label="Like"
                                        className={`feedback-icon like ${feedback[msg.id] === 'like' ? 'selected' : ''}`}
                                        onClick={() => setFeedback(prev => ({ ...prev, [msg.id]: prev[msg.id] === 'like' ? undefined : 'like' }))}
                                        title="Like"
                                    >
                                        <ThumbsUp size={16} />
                                    </button>
                                    <button
                                        type="button"
                                        aria-label="Dislike"
                                        className={`feedback-icon dislike ${feedback[msg.id] === 'dislike' ? 'selected' : ''}`}
                                        onClick={() => setFeedback(prev => ({ ...prev, [msg.id]: prev[msg.id] === 'dislike' ? undefined : 'dislike' }))}
                                        title="Dislike"
                                    >
                                        <ThumbsDown size={16} />
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area */}
            <form onSubmit={handleSend} className="chat-input-bar">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message..."
                    disabled={isLoading || !sessionId}
                    className="chat-input-field"
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            handleSend(e as any);
                        }
                    }}
                />
                <button
                    type="submit"
                    disabled={!input.trim() || isLoading || !sessionId}
                    className="chat-send-button"
                >
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
};
