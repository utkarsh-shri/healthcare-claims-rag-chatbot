import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, BarChart2 } from 'lucide-react';

function RelevanceBar({ score }) {
  const pct = Math.round(score * 100);
  let barColor = 'bg-emerald-500';
  let textColor = 'text-emerald-700';
  let bgColor = 'bg-emerald-50';
  if (score < 0.85 && score >= 0.70) {
    barColor = 'bg-amber-400';
    textColor = 'text-amber-700';
    bgColor = 'bg-amber-50';
  } else if (score < 0.70) {
    barColor = 'bg-red-400';
    textColor = 'text-red-700';
    bgColor = 'bg-red-50';
  }

  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${bgColor} ${textColor}`}>
        {pct}%
      </span>
    </div>
  );
}

export default function SourceCitations({ sources }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 border border-slate-200 rounded-lg overflow-hidden">
      {/* Toggle Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-50 hover:bg-slate-100 transition-colors duration-150 text-left"
      >
        <div className="flex items-center gap-2">
          <BarChart2 className="w-3.5 h-3.5 text-orange-600" />
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
            Source Citations
          </span>
          <span className="bg-orange-100 text-orange-700 text-xs font-bold px-1.5 py-0.5 rounded-full">
            {sources.length}
          </span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        )}
      </button>

      {/* Source List */}
      {isOpen && (
        <div className="divide-y divide-slate-100">
          {sources.map((source, index) => (
            <div key={index} className="px-3 py-3 bg-white">
              {/* Document name + relevance */}
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="flex items-center gap-1.5 min-w-0">
                  <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="text-xs font-semibold text-slate-700 truncate">
                    {source.document}
                  </span>
                </div>
              </div>
              <RelevanceBar score={source.relevance_score} />
              {/* Excerpt */}
              {source.excerpt && (
                <p className="mt-2 text-xs text-slate-500 leading-relaxed line-clamp-3 italic border-l-2 border-slate-200 pl-2">
                  {source.excerpt}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
