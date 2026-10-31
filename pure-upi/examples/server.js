// Runnable demo, no dependencies:
//   UPI_ID=yourname@okaxis UPI_NAME="My Site" node examples/server.js
// then open http://localhost:3000 (buyer) and http://localhost:3000/admin.html (approve payments).
// Login here is a fake cookie for the demo - use your real auth (JWT / session) in your app.

import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { createUpiPay, upiHandler } from '../src/index.js';

const here = (p) => fileURLToPath(new URL(p, import.meta.url));
const PORT = Number(process.env.PORT) || 3000;
const ADMIN = 'admin';

const premiumUsers = new Map(); // userId -> plan (use your User model)

const pay = createUpiPay({
  upiId: process.env.UPI_ID || 'demo@okaxis',
  name: process.env.UPI_NAME || 'Demo Site',
  plans: { monthly: { price: 99, name: 'Premium - 1 month' }, yearly: { price: 799, name: 'Premium - 1 year' } },
  notePrefix: 'Premium',
  onSubmitted: (o) => console.log(`[upi] UTR ${o.utr} submitted for ₹${o.amount} (order ${o.id}, user ${o.userId})`),
  onApproved: (o) => premiumUsers.set(o.userId, o.plan),
});

const cookies = (req) => Object.fromEntries((req.headers.cookie || '').split(';').filter(Boolean).map((c) => {
  const [k, ...v] = c.trim().split('=');
  return [k, decodeURIComponent(v.join('='))];
}));
const getUser = (req) => cookies(req).user || null;

const api = upiHandler(pay, { getUser, isAdmin: (req) => getUser(req) === ADMIN, basePath: '/api/upi' });

const STATIC = {
  '/': ['index.html', 'text/html'],
  '/admin.html': ['admin.html', 'text/html'],
  '/lib/client.js': ['../src/client.js', 'text/javascript'],
};

http.createServer(async (req, res) => {
  const { pathname } = new URL(req.url, 'http://x');
  if (pathname.startsWith('/api/upi/')) return api(req, res);

  if (pathname === '/api/login' && req.method === 'POST') {
    let body = '';
    for await (const c of req) body += c;
    const name = String(JSON.parse(body || '{}').user || '').replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 30);
    res.setHeader('Set-Cookie', `user=${encodeURIComponent(name)}; Path=/; HttpOnly; SameSite=Lax`);
    return res.end(JSON.stringify({ user: name }));
  }
  if (pathname === '/api/me') {
    const user = getUser(req);
    res.setHeader('Content-Type', 'application/json');
    return res.end(JSON.stringify({ user, premium: user ? premiumUsers.get(user) ?? null : null }));
  }

  const file = STATIC[pathname];
  if (!file) {
    res.statusCode = 404;
    return res.end('Not found');
  }
  res.setHeader('Content-Type', `${file[1]}; charset=utf-8`);
  res.end(await readFile(here(file[0])));
}).listen(PORT, () => {
  console.log(`pure-upi demo: http://localhost:${PORT}  (admin: http://localhost:${PORT}/admin.html, login as "${ADMIN}")`);
  console.log(`Payments go to ${pay.upiId}. Set UPI_ID=yourname@bank to scan with a real phone.`);
});
