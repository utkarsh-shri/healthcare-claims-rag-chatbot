import React, { useState, useRef, useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';
import { sendChatMessage } from '../api/chat';

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content: 'Hello. I\'m the Claims Adjudication Assistant, powered by Groq Llama 3.3 70B.\n\nI can help you with:\n• NCPDP reject code explanations and resolution steps\n• CMS Part D formulary and coverage guidelines\n• Prior authorization criteria for specialty medications\n• Formulary tier structures and step therapy protocols\n• RxClaim adjudication rules and pricing logic\n\nAll responses are grounded in your organization\'s knowledge base. How can I assist you today?',
  sources: [],
  pii_detected: false,
  response_time_ms: null,
};

function generateSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

export default function ChatWindow({ initialMessage }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId] = useState(generateSessionId);
  const bottomRef = useRef(null);

  // Auto-send a message if provided via sidebar quick-start
  useEffect(() => {
    if (initialMessage) {
      handleSend(initialMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (text) => {
    if (!text || isLoading) return;
    setError(null);

    // Optimistically add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await sendChatMessage(text, sessionId);
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        pii_detected: data.pii_detected,
        response_time_ms: data.response_time_ms,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const detail = err?.response?.data?.detail || err?.message || '';
      let errText = 'An unexpected error occurred. Please try again.';

      if (detail.toLowerCase().includes('quota') || detail.toLowerCase().includes('rate') || err?.response?.status === 429) {
        errText = '⚠️ Groq API rate limit reached. Please wait 30–60 seconds and try again. (Free tier: limited requests per minute)';
      } else if (detail) {
        errText = detail;
      }
      setError(errText);

    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Error Banner */}
      {error && (
        <div className="flex items-start gap-3 mx-4 mt-3 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" />
          <span className="flex-1">{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Info Banner */}
      <div className="flex items-start gap-3 mx-4 mt-3 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700 justify-center">
        <span>⚡ Note: First response may take 30s if the free backend service is waking up.</span>
      </div>

      {/* Message Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-thin">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role}
            content={msg.content}
            sources={msg.sources}
            pii_detected={msg.pii_detected}
            response_time_ms={msg.response_time_ms}
          />
        ))}

        {/* Typing indicator */}
        {isLoading && <MessageBubble isTyping />}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Input Bar */}
      <InputBar onSend={handleSend} isLoading={isLoading} />
    </div>
  );
}
