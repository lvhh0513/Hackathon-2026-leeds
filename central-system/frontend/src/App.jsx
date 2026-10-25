import React, { Component, useCallback, useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { EyeJourneyLogin } from './components/screens/EyeJourneyLogin';
import { centralApi, UNAUTHENTICATED_EVENT } from './api/centralApiClient';
import { USE_MOCK_DATA } from './config';

// The scanner runs as a separate local Streamlit service for the hackathon demo.
// This iframe is visual integration only: Streamlit is not protected by React authentication.
const SCANNER_URL = import.meta.env.VITE_SCANNER_URL || 'http://localhost:8501';

function ScannerPage({ user, onLogout }) {
  return (
    <main style={{ minHeight: '100vh', background: '#18100e', color: '#f8ede6', fontFamily: 'Inter, Arial, sans-serif' }}>
      <header style={{ padding: '20px clamp(20px, 4vw, 64px)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        <strong style={{ letterSpacing: '0.12em' }}>RETINA<span style={{ color: '#e45b45' }}>TRANSFORM</span></strong>
        <button type="button" onClick={onLogout} style={{ padding: '12px 18px', color: 'white', background: '#a72c25', border: '1px solid #ed6756', cursor: 'pointer' }}>LOG OUT</button>
      </header>
      <section style={{ padding: '4px clamp(20px, 4vw, 64px) 24px' }}>
        <p style={{ color: '#eb8c73', letterSpacing: '0.18em', fontSize: '0.8rem', marginBottom: 8 }}>SCREENING PORTAL</p>
        <h1 style={{ fontSize: 'clamp(1.5rem, 3vw, 2.4rem)', lineHeight: 1.2, margin: '0 0 10px' }}>Welcome{user?.name ? `, ${user.name}` : ''}.</h1>
        <p style={{ color: '#c7aea5', margin: '0 0 10px' }}>Your retinal screening assistant is below. Use public or synthetic test images only.</p>
        <p style={{ margin: '0 0 16px', fontSize: '0.9rem' }}>
          <a href={SCANNER_URL} target="_blank" rel="noopener noreferrer" style={{ color: '#eb8c73' }}>Open scanner in a separate tab</a>
          <span style={{ color: '#c7aea5' }}> if the embedded view doesn't load.</span>
        </p>
        <iframe
          title="RetinaTransform retinal screening assistant"
          src={SCANNER_URL}
          style={{ display: 'block', width: '100%', height: 'max(740px, 82vh)', border: '1px solid #55362e', borderRadius: 12, background: '#fff' }}
          allow="clipboard-read; clipboard-write"
        />
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
      <Route path="/" element={user ? <Navigate to="/scanner" replace /> : <EyeJourneyLogin skippAuth={true} onLogin={handleLogin} />} />
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
