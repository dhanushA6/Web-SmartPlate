import { useEffect, useRef } from 'react';

export default function ChatBox({ messages }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={containerRef}
      className="h-96 overflow-y-auto border border-slate-200 rounded-xl bg-white p-4 space-y-4"
    >
      {messages.length === 0 && (
        <p className="text-sm text-slate-500">
          Start by asking a diabetes nutrition question or request food recommendations for a meal.
        </p>
      )}
      {messages.map((m, idx) => (
        <div
          key={idx}
          className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
            m.role === 'user'
              ? 'ml-auto bg-brand-600 text-white'
              : 'mr-auto bg-slate-100 text-slate-900'
          }`}
        >
          <p className="whitespace-pre-line">{m.text}</p>
        </div>
      ))}
    </div>
  );
}

