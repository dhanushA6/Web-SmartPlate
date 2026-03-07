import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown'; // Added for formatting
import ChatBox from '../components/ChatBox';
import { askAssistant, predictNutrition } from '../api/apiClient';

const modes = [
  { value: 'normal', label: 'Normal mode' },
  { value: 'food_recommendation', label: 'Food recommendation' }
];

const meals = [
  { value: 'breakfast', label: 'Breakfast' },
  { value: 'lunch', label: 'Lunch' },
  { value: 'snacks', label: 'Snacks' },
  { value: 'dinner', label: 'Dinner' }
];

export default function Assistant() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');

  const [mode, setMode] = useState('normal');
  const [mealType, setMealType] = useState('breakfast');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nutrition, setNutrition] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!userId) {
      navigate('/login');
    }
  }, [userId, navigate]);

  useEffect(() => {
    const fetchNutrition = async () => {
      if (!userId) return;
      try {
        const { data } = await predictNutrition(userId);
        setNutrition(data);
      } catch (err) {
        console.error("Failed to fetch nutrition context", err);
      }
    };
    fetchNutrition();
  }, [userId]);

  const handleSend = async () => {
    if (!input.trim() || !userId) return;
    setError('');
    
    const userMessage = { role: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const { data } = await askAssistant({
        user_id: userId,
        message: input,
        mode,
        meal_type: mode === 'food_recommendation' ? mealType : null
      });
      
      setMessages((prev) => [...prev, { role: 'assistant', text: data.answer }]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Assistant request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="layout-main space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Personalized Assistant</h1>
          <p className="text-sm text-slate-500">
            Ask diabetes nutrition questions or request structured meal recommendations.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <div>
            <p className="text-xs font-medium text-slate-500 mb-1">Mode</p>
            <select
              className="input-field"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
            >
              {modes.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          {mode === 'food_recommendation' && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Meal type</p>
              <select
                className="input-field"
                value={mealType}
                onChange={(e) => setMealType(e.target.value)}
              >
                {meals.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="flex flex-col h-[600px] bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
          {/* Chat Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none' 
                    : 'bg-white text-slate-700 border border-slate-200 rounded-tl-none'
                }`}>
                  {msg.role === 'user' ? (
                    msg.text
                  ) : (
                    <div className="prose prose-sm prose-slate max-w-none prose-p:leading-relaxed prose-li:my-1">
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* AI Loading State */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-4 shadow-sm">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                  </div>
                </div>
              </div>
            )}
            
            {error && (
              <div className="text-center p-2 text-xs text-red-500 font-medium bg-red-50 rounded-lg">
                {error}
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 bg-white border-t border-slate-200">
            <div className="flex items-end gap-3">
              <textarea
                rows={2}
                className="input-field flex-1 resize-none bg-slate-50 focus:bg-white transition-colors"
                placeholder={mode === 'normal' ? 'Ask about nutrition...' : 'Request a meal plan...'}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
              <button
                type="button"
                className="primary-btn h-11 px-6 disabled:opacity-50 flex items-center justify-center min-w-[80px]"
                onClick={handleSend}
                disabled={loading || !input.trim()}
              >
                {loading ? (
                   <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                ) : 'Send'}
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar Info */}
        <aside className="space-y-3">
          <div className="card shadow-sm border-slate-200">
            <div className="card-header border-b border-slate-100 bg-slate-50/50">
              <h2 className="card-title text-sm font-bold text-slate-800 uppercase tracking-tight">Macro Summary</h2>
            </div>
            <div className="card-body p-4 space-y-4 text-sm">
              {!nutrition ? (
                <p className="text-slate-500 italic">No prediction data yet.</p>
              ) : (
                <>
                  <p className="text-slate-900 font-bold border-b pb-1">Daily Targets</p>
                  <ul className="space-y-3 text-slate-600">
                    <li className="flex justify-between"><span>Calories:</span> <span className="font-mono font-semibold">{nutrition.daily.daily_calories_kcal.toFixed(0)} kcal</span></li>
                    <li className="flex justify-between"><span>Carbs:</span> <span className="font-mono font-semibold">{nutrition.daily.daily_carbohydrates_g.toFixed(1)}g</span></li>
                    <li className="flex justify-between"><span>Protein:</span> <span className="font-mono font-semibold">{nutrition.daily.daily_protein_g.toFixed(1)}g</span></li>
                    <li className="flex justify-between"><span>Fat:</span> <span className="font-mono font-semibold">{nutrition.daily.daily_fat_g.toFixed(1)}g</span></li>
                    <li className="flex justify-between"><span>Fiber:</span> <span className="font-mono font-semibold text-green-600">{nutrition.daily.daily_fiber_g.toFixed(1)}g</span></li>
                  </ul>
                </>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}