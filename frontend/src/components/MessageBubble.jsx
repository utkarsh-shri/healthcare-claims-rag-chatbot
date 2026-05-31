import React from 'react';
import { User, Bot, ShieldAlert, Clock } from 'lucide-react';
import SourceCitations from './SourceCitations';

function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-700 flex items-center justify-center shadow-sm">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex items-center gap-1.5 h-4">
          <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

function UserMessage({ content }) {
  return (
    <div className="flex items-start gap-3 mb-4 flex-row-reverse">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center shadow-sm">
        <User className="w-4 h-4 text-slate-600" />
      </div>
      <div className="max-w-[75%]">
        <div className="bg-blue-700 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    </div>
  );
}

function AssistantMessage({ content, sources, pii_detected, response_time_ms }) {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-700 flex items-center justify-center shadow-sm">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="max-w-[80%]">
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">{content}</p>

          {/* Source citations */}
          <SourceCitations sources={sources} />

          {/* Footer metadata */}
          <div className="flex items-center gap-3 mt-2.5 pt-2 border-t border-slate-100">
            {response_time_ms && (
              <span className="flex items-center gap-1 text-xs text-slate-400">
                <Clock className="w-3 h-3" />
                {response_time_ms}ms
              </span>
            )}
            {pii_detected && (
              <span className="flex items-center gap-1 text-xs text-amber-600 font-medium">
                <ShieldAlert className="w-3 h-3" />
                PII detected &amp; masked
              </span>
            )}
            <span className="text-xs text-slate-400 ml-auto">
              Llama 3.1 8B · RAG
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MessageBubble({ role, content, sources, pii_detected, response_time_ms, isTyping }) {
  if (isTyping) return <TypingIndicator />;
  if (role === 'user') return <UserMessage content={content} />;
  return (
    <AssistantMessage
      content={content}
      sources={sources}
      pii_detected={pii_detected}
      response_time_ms={response_time_ms}
    />
  );
}
