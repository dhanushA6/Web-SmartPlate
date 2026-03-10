import { Link, NavLink, useNavigate } from 'react-router-dom';

const navItemClass =
  'px-3 py-2 text-sm font-medium rounded-lg transition-colors hover:bg-slate-100';

export default function Navbar() {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('profileCompleted');
    navigate('/login');
  };

  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-brand-500 flex items-center justify-center text-white text-sm font-bold">
            DN
          </div>
          <Link
            to="/"
            className="text-sm sm:text-base font-semibold text-slate-900 tracking-tight"
          >
            Diabetes Nutrition & Assistant
          </Link>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          {userId ? (
            <>
              <NavLink
                to="/assistant"
                className={({ isActive }) =>
                  `${navItemClass} ${
                    isActive ? 'bg-slate-900 text-white' : 'text-slate-700'
                  }`
                }
              >
                Dashboard
              </NavLink>
              <NavLink
                to="/nutrition"
                className={({ isActive }) =>
                  `${navItemClass} ${
                    isActive ? 'bg-slate-900 text-white' : 'text-slate-700'
                  }`
                }
              >
                Nutrition
              </NavLink>
              <NavLink
                to="/food-recommendation"
                className={({ isActive }) =>
                  `${navItemClass} ${
                    isActive ? 'bg-slate-900 text-white' : 'text-slate-700'
                  }`
                }
              >
                Food Plan
              </NavLink>
              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  `${navItemClass} ${
                    isActive ? 'bg-slate-900 text-white' : 'text-slate-700'
                  }`
                }
              >
                Profile
              </NavLink>
            </>
          ) : null}
        </nav>

        <div className="flex items-center gap-2">
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
    </header>
  );
}

