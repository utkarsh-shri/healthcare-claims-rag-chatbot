import React, { useState, useEffect } from 'react';
import {
  Shield, ChevronRight, Activity, Zap,
  FileSearch, ClipboardList, PillIcon, BookOpen, AlertTriangle
} from 'lucide-react';
import ChatWindow from './components/ChatWindow';
import { getHealth } from './api/chat';

const EXAMPLE_QUERIES = [
  {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    label: 'Reject Code 75',
    query: 'What does NCPDP reject code 75 mean and how do I resolve it?',
  },
  {
    icon: <FileSearch className="w-3.5 h-3.5" />,
    label: 'Prior Auth — TNF Inhibitors',
    query: 'What are the prior authorization criteria for TNF inhibitors like adalimumab?',
  },
  {
    icon: <PillIcon className="w-3.5 h-3.5" />,
    label: 'GLP-1 Coverage',
    query: 'What are the formulary requirements for GLP-1 agonists like semaglutide?',
  },
  {
    icon: <ClipboardList className="w-3.5 h-3.5" />,
    label: 'Part D Transition Fill',
    query: 'What is the CMS transition fill policy for new Part D enrollees?',
  },
  {
    icon: <BookOpen className="w-3.5 h-3.5" />,
    label: 'Step Therapy Protocol',
    query: 'Explain the step therapy requirements for specialty biologics.',
  },
];

function StatusBadge({ status }) {
  if (!status) return <span className="text-xs text-slate-400">Connecting…</span>;
  const isHealthy = status === 'healthy';
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
      isHealthy ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
      {isHealthy ? 'Backend Online' : 'Degraded'}
    </span>
  );
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [chatKey, setChatKey] = useState(0);
  const [activeSuggestion, setActiveSuggestion] = useState(null);

  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth({ status: 'degraded' }));
  }, []);

  const handleSuggestionClick = (query) => {
    setActiveSuggestion(query);
    setChatKey((k) => k + 1);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-100 overflow-hidden">
      {/* ── Header Bar ─────────────────────────────────────── */}
      <header className="flex-shrink-0 h-14 bg-blue-900 flex items-center px-5 gap-3 shadow-lg z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-white/10 rounded-md flex items-center justify-center border border-white/20">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white leading-tight tracking-wide">
              Claims Adjudication Assistant
            </h1>
            <p className="text-xs text-blue-200 leading-tight">Pharmacy Benefit Management</p>
          </div>
        </div>

        <div className="h-5 w-px bg-white/20 mx-1" />

        <span className="text-xs font-medium bg-blue-700 text-blue-100 border border-blue-600 px-2 py-0.5 rounded-md tracking-wide">
          AI-Powered · Beta
        </span>

        <div className="ml-auto flex items-center gap-3">
          <StatusBadge status={health?.status} />
          {health?.document_count > 0 && (
            <span className="text-xs text-blue-300">
              {health.document_count} chunks indexed
            </span>
          )}
        </div>
      </header>

      {/* ── Main Layout ────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Sidebar ──────────────────────────────────────── */}
        <aside className="w-64 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col overflow-y-auto">

          {/* Session Info */}
          <div className="px-4 pt-5 pb-3 border-b border-slate-100">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">Session</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Model</span>
                <span className="font-medium text-slate-700 flex items-center gap-1">
                  <Zap className="w-3 h-3 text-blue-500" />
                  Groq Llama 3.3 70B
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Pipeline</span>
                <span className="font-medium text-slate-700">RAG · Supabase pgvector</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Embeddings</span>
                <span className="font-medium text-slate-700">fastembed (all-MiniLM-L6)</span>
              </div>
            </div>
          </div>

          {/* Knowledge Base */}
          <div className="px-4 py-4 border-b border-slate-100">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">Knowledge Base</p>
            <div className="space-y-1.5">
              {[
                'NCPDP Reject Codes',
                'CMS Part D Guidelines',
                'RxClaim Adjudication Rules',
                'Prior Auth Requirements',
                'Formulary Tier Structure',
              ].map((doc) => (
                <div key={doc} className="flex items-center gap-2 text-xs text-slate-600 py-0.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  {doc}
                </div>
              ))}
            </div>
          </div>

          {/* Example Queries */}
          <div className="px-4 py-4 flex-1">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">Quick Start</p>
            <div className="space-y-1.5">
              {EXAMPLE_QUERIES.map((item) => (
                <button
                  key={item.label}
                  onClick={() => handleSuggestionClick(item.query)}
                  className="w-full flex items-start gap-2 text-left px-2.5 py-2 rounded-lg text-xs text-slate-600 hover:bg-blue-50 hover:text-blue-700 transition-colors duration-100 group"
                >
                  <span className="mt-0.5 text-slate-400 group-hover:text-blue-500 flex-shrink-0">
                    {item.icon}
                  </span>
                  <span className="flex-1 leading-snug">{item.label}</span>
                  <ChevronRight className="w-3 h-3 mt-0.5 text-slate-300 group-hover:text-blue-400 flex-shrink-0" />
                </button>
              ))}
            </div>
          </div>

          {/* Footer note */}
          <div className="px-4 py-3 border-t border-slate-100">
            <p className="text-xs text-slate-400 leading-relaxed">
              Responses are grounded in the configured knowledge base. Always verify clinical decisions with authorized sources.
            </p>
          </div>
        </aside>

        {/* ── Chat Area ────────────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden bg-slate-50">
          <ChatWindow
            key={chatKey}
            initialMessage={activeSuggestion}
          />
        </main>
      </div>
    </div>
  );
}
