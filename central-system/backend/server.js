'use strict';
// RetinaTransform: portable SQLite authentication backend (local hackathon demo).
// No clinical data or retinal images are stored by this service.
require('dotenv').config({ path: require('path').join(__dirname, '.env') });
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { DatabaseSync } = require('node:sqlite');
const express = require('express');
const cookieParser = require('cookie-parser');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const PORT = Number(process.env.PORT || 5000);
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET || JWT_SECRET.length < 32 || JWT_SECRET.startsWith('REPLACE_')) {
  console.error('Set JWT_SECRET to a random 32+ character value in backend/.env');
  process.exit(1);
}
const DB_PATH = path.resolve(__dirname, process.env.SQLITE_PATH || './data/retinatransform.sqlite');
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
const db = new DatabaseSync(DB_PATH);
db.exec(`PRAGMA busy_timeout = 5000; PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);`);
const lookup = db.prepare('SELECT user_id, name, email, password_hash, is_active FROM users WHERE email = ?');
const lookupId = db.prepare('SELECT user_id, name, email, is_active FROM users WHERE user_id = ?');
const insert = db.prepare('INSERT INTO users (user_id, name, email, password_hash) VALUES (?, ?, ?, ?)');
const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '32kb' }));
app.use(cookieParser());
app.use((_req, res, next) => {
  res.set('Cache-Control', 'no-store');
  res.set('X-Content-Type-Options', 'nosniff');
  res.set('X-Frame-Options', 'DENY');
  next();
});
const cookieName = 'rt_session';
const cookieOptions = { httpOnly: true, sameSite: 'lax', secure: process.env.NODE_ENV === 'production', path: '/' };
const maxAge = 24 * 60 * 60 * 1000;
function publicUser(u) {
  // Compatibility only with Indi's existing frontend: this is NOT a medical qualification.
  return { userId: u.user_id, id: u.user_id, name: u.name, email: u.email, role: 'ophthalmologist' };
}
function csrfFor(token) { return crypto.createHmac('sha256', JWT_SECRET).update(`csrf:${token}`).digest('hex'); }
function createSession(res, u) {
  const token = jwt.sign({ sub: u.user_id }, JWT_SECRET, { issuer: 'retinatransform', expiresIn: '24h' });
  res.cookie(cookieName, token, { ...cookieOptions, maxAge });
  return { user: publicUser(u), csrfToken: csrfFor(token), expiresAt: new Date(Date.now() + maxAge).toISOString() };
}
function currentSession(req) {
  const token = req.cookies?.[cookieName];
  if (!token) return null;
  try {
    const { sub } = jwt.verify(token, JWT_SECRET, { issuer: 'retinatransform' });
    const user = lookupId.get(sub);
    return user && user.is_active ? { user, token } : null;
  } catch { return null; }
}
// In-memory, single-process demo login rate limiting.
const attempts = new Map();
function rateLimit(req, res, next) {
  const key = `${req.ip}:${String(req.body?.email || '').trim().toLowerCase()}`;
  const now = Date.now();
  if (attempts.size > 2000) attempts.clear();
  const entry = attempts.get(key);
  if (entry && now - entry.since < 15 * 60_000 && entry.count >= 10) {
    return res.status(429).json({ error: 'rate_limited', message: 'Too many attempts. Try again later.' });
  }
  req.attemptKey = key;
  next();
}
function failedLogin(key) {
  const now = Date.now(); const entry = attempts.get(key);
  attempts.set(key, !entry || now - entry.since > 15 * 60_000
    ? { since: now, count: 1 } : { ...entry, count: entry.count + 1 });
}
const fallbackHash = bcrypt.hashSync('dummy-password-not-valid', 12);
// Frontend and API should be accessed through Vite's same-origin proxy.
app.use((req, res, next) => {
  if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) return next();
  const origin = req.get('origin');
  const allowedOrigins = (process.env.APP_ORIGIN || 'http://localhost:5174').split(',').map(x => x.trim());
  if (origin && !allowedOrigins.includes(origin)) return res.status(403).json({ error: 'forbidden_origin', message: 'Unexpected request origin.' });
  next();
});
app.get('/health', (_req, res) => res.json({ status: 'ok', database: 'sqlite' }));
app.post('/api/v1/auth/register', rateLimit, async (req, res, next) => {
  try {
    const name = typeof req.body?.name === 'string' ? req.body.name.trim() : '';
    const email = typeof req.body?.email === 'string' ? req.body.email.trim().toLowerCase() : '';
    const password = req.body?.password;
    if (name.length < 2 || name.length > 100 || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
      || typeof password !== 'string' || password.length < 12 || password.length > 72) {
      return res.status(400).json({ error: 'invalid_input', message: 'Enter a name, valid email and a password between 12 and 72 characters.' });
    }
    if (lookup.get(email)) return res.status(409).json({ error: 'email_exists', message: 'An account with that email already exists.' });
    const hash = await bcrypt.hash(password, 12);
    const id = crypto.randomUUID();
    try { insert.run(id, name, email, hash); }
    catch (e) {
      if (e.code === 'ERR_SQLITE_ERROR' && /UNIQUE constraint failed/i.test(e.message)) {
        return res.status(409).json({ error: 'email_exists', message: 'An account with that email already exists.' });
      }
      throw e;
    }
    return res.status(201).json(createSession(res, { user_id: id, name, email }));
  } catch (err) { next(err); }
});
app.post('/api/v1/auth/login', rateLimit, async (req, res, next) => {
  try {
    const email = typeof req.body?.email === 'string' ? req.body.email.trim().toLowerCase() : '';
    const password = req.body?.password;
    if (!email || typeof password !== 'string') return res.status(400).json({ error: 'invalid_input', message: 'Email and password are required.' });
    const user = lookup.get(email);
    const matches = await bcrypt.compare(password, user?.password_hash || fallbackHash);
    if (!matches || !user?.is_active) {
      failedLogin(req.attemptKey);
      return res.status(401).json({ error: 'invalid_credentials', message: 'Email or password is incorrect.' });
    }
    attempts.delete(req.attemptKey);
    return res.json(createSession(res, user));
  } catch (err) { next(err); }
});
app.get('/api/v1/auth/me', (req, res) => {
  const session = currentSession(req);
  if (!session) return res.status(401).json({ error: 'unauthenticated', message: 'Not logged in.' });
  res.json({ user: publicUser(session.user), csrfToken: csrfFor(session.token) });
});
app.post('/api/v1/auth/logout', (_req, res) => {
  res.clearCookie(cookieName, cookieOptions);
  res.status(204).end();
});
app.get('/api/v1/scanner/status', (req, res) => {
  if (!currentSession(req)) return res.status(401).json({ error: 'unauthenticated' });
  res.json({ status: 'awaiting_yuta_integration' });
});
app.use((_req, res) => res.status(404).json({ error: 'not_found' }));
app.use((err, _req, res, _next) => {
  console.error('Backend error:', err);
  res.status(500).json({ error: 'server_error', message: 'Unexpected server error.' });
});
app.listen(PORT, '127.0.0.1', () => console.log(`RetinaTransform SQLite backend: http://localhost:${PORT}\nDatabase: ${DB_PATH}`));
