import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Nutrition from './pages/Nutrition';
import Assistant from './pages/Assistant';

function RequireAuth({ children }) {
  const userId = localStorage.getItem('userId');
  if (!userId) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <div className="layout-shell">
      <Navbar />
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
        <Route
          path="/nutrition"
          element={
            <RequireAuth>
              <Nutrition />
            </RequireAuth>
          }
        />
        <Route
          path="/assistant"
          element={
            <RequireAuth>
              <Assistant />
            </RequireAuth>
          }
        />
      </Routes>
    </div>
  );
}

