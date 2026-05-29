import React, { useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

export default function InputBar({ onSend, isLoading }) {
  const textareaRef = useRef(null);
  const MAX_CHARS = 500;
  const [value, setValue] = React.useState('');

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 96) + 'px'; // max ~3 rows
  }, [value]);

  const canSend = value.trim().length > 0 && !isLoading && value.length <= MAX_CHARS;

  const handleSend = () => {
    if (!canSend) return;
    onSend(value.trim());
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const charsLeft = MAX_CHARS - value.length;
  const isNearLimit = charsLeft <= 50;
  const isOverLimit = charsLeft < 0;

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3">
      <div className={`flex items-end gap-3 rounded-xl border transition-colors duration-150 px-3 py-2.5 ${
        isOverLimit
          ? 'border-red-400 bg-red-50'
          : 'border-slate-300 bg-white focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100'
      }`}>
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder="Ask about claim adjudication, reject codes, formulary tiers, prior auth requirements…"
          className="flex-1 resize-none bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none leading-relaxed disabled:opacity-60"
          style={{ maxHeight: '96px', overflowY: 'auto' }}
        />

        {/* Right side: char counter + send */}
        <div className="flex items-center gap-2 flex-shrink-0 self-end pb-0.5">
          {isNearLimit && (
            <span className={`text-xs font-medium tabular-nums ${isOverLimit ? 'text-red-500' : 'text-amber-500'}`}>
              {charsLeft}
            </span>
          )}
          <button
            onClick={handleSend}
            disabled={!canSend}
            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150 ${
              canSend
                ? 'bg-blue-700 hover:bg-blue-800 text-white shadow-sm hover:shadow-md active:scale-95'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
          >
            {isLoading
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Send className="w-4 h-4" />
            }
          </button>
        </div>
      </div>

      {/* Helper text */}
      <p className="text-xs text-slate-400 mt-1.5 px-1">
        Press <kbd className="px-1 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-500 text-xs">Enter</kbd> to send,&nbsp;
        <kbd className="px-1 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-500 text-xs">Shift+Enter</kbd> for a new line.
      </p>
    </div>
  );
}
