import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Salad, Menu, X } from 'lucide-react';

const navItemClass =
  'px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200 hover:bg-slate-100';
const navItemActiveClass = 'bg-brand-600 text-white hover:bg-brand-500';

export default function Navbar() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('profileCompleted');
    navigate('/login');
  };

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-sm shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-xl bg-brand-500 flex items-center justify-center text-white shadow-md flex-shrink-0">
            <Salad size={18} strokeWidth={2.5} />
          </div>
          <Link
            to="/"
            className="text-sm sm:text-base font-semibold text-slate-900 tracking-tight hover:text-brand-600 transition-colors"
          >
            Smart Plate
          </Link>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          {userId ? (
            <>
              <NavLink to="/assistant" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`}>Nutrition Assistant</NavLink>
              <NavLink to="/nutrition" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`}>Nutrition</NavLink>
              <NavLink to="/suitability-check" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`}>Suitability Check</NavLink>
              <NavLink to="/food-recommendation" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`}>Food Plan</NavLink>
              <NavLink to="/profile" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`}>Profile</NavLink>
            </>
          ) : null}
        </nav>

        <div className="flex items-center gap-2">
          {userId && (
            <button
              type="button"
              onClick={() => setMobileOpen((o) => !o)}
              className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          )}
          {!userId ? (
            <>
              <Link to="/login" className="secondary-btn text-xs sm:text-sm">
                Login
              </Link>
              <Link to="/register" className="primary-btn text-xs sm:text-sm">
                Register
              </Link>
            </>
          ) : (
            <button
              type="button"
              onClick={handleLogout}
              className="secondary-btn text-xs sm:text-sm"
            >
              Logout
            </button>
          )}
        </div>
      </div>

      {userId && mobileOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 py-3 flex flex-col gap-1">
          <NavLink to="/assistant" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`} onClick={() => setMobileOpen(false)}>Nutrition Assistant</NavLink>
          <NavLink to="/nutrition" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`} onClick={() => setMobileOpen(false)}>Nutrition</NavLink>
          <NavLink to="/suitability-check" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`} onClick={() => setMobileOpen(false)}>Suitability Check</NavLink>
          <NavLink to="/food-recommendation" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`} onClick={() => setMobileOpen(false)}>Food Plan</NavLink>
          <NavLink to="/profile" className={({ isActive }) => `${navItemClass} ${isActive ? navItemActiveClass : 'text-slate-700'}`} onClick={() => setMobileOpen(false)}>Profile</NavLink>
        </div>
      )}
    </header>
  );
}

