import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registerUser } from '../api/apiClient';

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ user_id: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      await registerUser(form);
      setSuccess('Account created. You can now sign in.');
      setTimeout(() => navigate('/login'), 1000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout-main flex items-center justify-center">
      <div className="card w-full max-w-md">
        <div className="card-header">
          <h1 className="card-title">Create account</h1>
        </div>
        <div className="card-body space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 border border-red-100">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700 border border-emerald-100">
              {success}
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
                required
              />
            </div>
            <button type="submit" className="primary-btn w-full" disabled={loading}>
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>
          <p className="text-xs text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-600 font-medium">
              Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

