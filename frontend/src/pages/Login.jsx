import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { loginUser } from '../api/apiClient';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ user_id: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await loginUser(form);
      localStorage.setItem('userId', data.user_id);
      localStorage.setItem('profileCompleted', String(data.profile_completed));
      if (data.profile_completed) {
        navigate('/nutrition');
      } else {
        navigate('/profile');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout-main flex items-center justify-center">
      <div className="card w-full max-w-md">
        <div className="card-header">
          <h1 className="card-title">Sign in</h1>
        </div>
        <div className="card-body space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 border border-red-100">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label" htmlFor="user_id">
                User ID
              </label>
              <input
                id="user_id"
                name="user_id"
                className="input-field"
                value={form.user_id}
                onChange={handleChange}
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                className="input-field"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
                required
              />
            </div>
            <button type="submit" className="primary-btn w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
          <p className="text-xs text-slate-500">
            Do not have an account?{' '}
            <Link to="/register" className="text-brand-600 font-medium">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

