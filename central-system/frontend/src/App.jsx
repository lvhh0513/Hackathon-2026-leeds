import React, { Component, useCallback, useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { EyeJourneyLogin } from './components/screens/EyeJourneyLogin';
import { centralApi, UNAUTHENTICATED_EVENT } from './api/centralApiClient';
import { USE_MOCK_DATA } from './config';

// The scanner is a temporary landing area until Yuta's Streamlit application is connected.
// No old medical dashboards or backend endpoints are needed to render it.
function ScannerPage({ user, onLogout }) {
  return (
    <main style={{ minHeight: '100vh', background: '#18100e', color: '#f8ede6', padding: 'clamp(24px, 5vw, 80px)', fontFamily: 'Inter, Arial, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        <strong style={{ letterSpacing: '0.12em' }}>RETINA<span style={{ color: '#e45b45' }}>TRANSFORM</span></strong>
        <button type="button" onClick={onLogout} style={{ padding: '12px 18px', color: 'white', background: '#a72c25', border: '1px solid #ed6756', cursor: 'pointer' }}>LOG OUT</button>
      </div>
      <section style={{ maxWidth: 760, margin: '12vh auto 0' }}>
        <p style={{ color: '#eb8c73', letterSpacing: '0.18em' }}>SCREENING PORTAL</p>
        <h1 style={{ fontSize: 'clamp(2.5rem, 6vw, 4.5rem)', lineHeight: 1.1 }}>Welcome{user?.name ? `, ${user.name}` : ''}.</h1>
        <p style={{ color: '#c7aea5', fontSize: '1.1rem', lineHeight: 1.7 }}>Your account is signed in. Yuta's existing Python + Streamlit retinal scanner will be connected here.</p>
        <p style={{ color: '#dfaa97', fontSize: '0.9rem' }}>Scanner integration pending — no scan is being performed yet.</p>
      </section>
    </main>
  );
}

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, details) { console.error('RetinaTransform render error:', error, details); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <main style={{ padding: 40, fontFamily: 'Arial, sans-serif' }}>
        <h1>APPLICATION ERROR</h1>
        <p>{this.state.error.message}</p>
        <button onClick={() => { window.location.href = '/'; }}>Return to home</button>
      </main>
    );
  }
}

function AppRoutes() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(USE_MOCK_DATA);

  // The real server, not localStorage, is the authority for active sessions.
  useEffect(() => {
    if (USE_MOCK_DATA) {
      const demoName = localStorage.getItem('netra_user_role');
      if (demoName) setUser({ name: 'Demo member', role: demoName });
      return;
    }
    let cancelled = false;
    centralApi.me()
      .then((session) => { if (!cancelled && session?.user) setUser(session.user); })
      .catch(() => { if (!cancelled) setUser(null); })
      .finally(() => { if (!cancelled) setAuthChecked(true); });
    return () => { cancelled = true; };
  }, []);

  const clearSession = useCallback(() => {
    setUser(null);
    localStorage.removeItem('netra_user_role');
    localStorage.removeItem('netra_user_profile');
  }, []);

  useEffect(() => {
    if (USE_MOCK_DATA) return undefined;
    const onUnauthenticated = () => {
      clearSession();
      navigate('/', { replace: true });
    };
    window.addEventListener(UNAUTHENTICATED_EVENT, onUnauthenticated);
    return () => window.removeEventListener(UNAUTHENTICATED_EVENT, onUnauthenticated);
  }, [clearSession, navigate]);

  // Compatible with EyeJourneyLogin's existing onLogin(role, email, serverUser).
  const handleLogin = (selectedRole, email, serverUser) => {
    if (USE_MOCK_DATA) {
      localStorage.setItem('netra_user_role', selectedRole || 'ophthalmologist');
    }
    setUser(serverUser || { name: email || 'Demo member', email, role: selectedRole || 'ophthalmologist' });
    setAuthChecked(true);
    navigate('/scanner', { replace: true });
  };

  const handleLogout = async () => {
    try {
      if (!USE_MOCK_DATA) await centralApi.logout();
    } catch (error) {
      console.warn('Could not end the server session:', error);
    } finally {
      clearSession();
      navigate('/', { replace: true });
    }
  };

  if (!authChecked) {
    return <div style={{ minHeight: '100vh', background: '#18100e', color: 'white', display: 'grid', placeItems: 'center' }}>Checking session…</div>;
  }

  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to="/scanner" replace /> : <EyeJourneyLogin onLogin={handleLogin} />} />
      <Route path="/scanner" element={user ? <ScannerPage user={user} onLogout={handleLogout} /> : <Navigate to="/" replace />} />
      <Route path="*" element={<Navigate to={user ? '/scanner' : '/'} replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ErrorBoundary>
  );
}
