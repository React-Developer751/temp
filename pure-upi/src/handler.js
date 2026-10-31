import { UpiPayError } from './errors.js';

const MAX_BODY = 16 * 1024;

function send(res, status, body) {
  if (res.headersSent) return;
  const json = JSON.stringify(body);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(json);
}

async function readBody(req) {
  if (req.body !== undefined && req.body !== null && typeof req.body === 'object' && !Buffer.isBuffer(req.body)) return req.body;
  if (typeof req.body === 'string' || Buffer.isBuffer(req.body)) return parse(String(req.body));
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY) throw new UpiPayError('BAD_REQUEST', 'Request body too large');
    chunks.push(chunk);
  }
  return parse(Buffer.concat(chunks).toString('utf8'));
}

function parse(text) {
  if (!text.trim()) return {};
  try {
    const body = JSON.parse(text);
    if (body && typeof body === 'object' && !Array.isArray(body)) return body;
  } catch { /* fall through */ }
  throw new UpiPayError('BAD_REQUEST', 'Body must be a JSON object');
}

const userIdOf = (user) => (user && typeof user === 'object' ? user.id ?? user._id : user);

/**
 * Node / Express request handler for a UpiPay instance.
 *
 *   app.use('/api/upi', upiHandler(pay, { getUser, isAdmin }))           // Express
 *   http.createServer(upiHandler(pay, { basePath: '/api/upi', ... }))     // plain Node
 *
 * getUser(req) -> user id (or { id } / { _id }) of the logged-in user, or null.
 * isAdmin(req) -> true for whoever may approve payments.
 */
export function upiHandler(pay, { getUser, isAdmin, basePath = '', qr = true, onError } = {}) {
  if (typeof getUser !== 'function') throw new TypeError('pure-upi: upiHandler needs getUser(req)');
  if (typeof isAdmin !== 'function') throw new TypeError('pure-upi: upiHandler needs isAdmin(req)');
  const base = basePath.replace(/\/+$/, '');

  async function requireUser(req) {
    const id = userIdOf(await getUser(req));
    if (id === undefined || id === null || id === '') throw new UpiPayError('UNAUTHORIZED', 'Login required');
    return String(id);
  }
  async function requireAdmin(req) {
    if (!(await isAdmin(req))) throw new UpiPayError('FORBIDDEN', 'Admin only');
  }
  const withQr = (order) => ({ order, link: pay.linkFor(order), ...(qr ? { qrSvg: pay.qrFor(order) } : {}) });

  async function route(req, res, path, query) {
    const method = req.method;
    let m;

    if (method === 'GET' && path === '/plans') return send(res, 200, { plans: pay.plans() });

    if (method === 'POST' && path === '/orders') {
      const userId = await requireUser(req);
      const { plan } = await readBody(req);
      const { order } = await pay.createOrder({ userId, plan });
      return send(res, 201, withQr(order));
    }

    if (method === 'GET' && path === '/orders') {
      const userId = await requireUser(req);
      return send(res, 200, { orders: await pay.list({ userId, limit: 50 }) });
    }

    if (method === 'GET' && (m = /^\/orders\/([A-Za-z0-9]{1,64})$/.exec(path))) {
      const userId = await requireUser(req);
      const order = await pay.getOrder(m[1]);
      if (order.userId !== userId && !(await isAdmin(req))) throw new UpiPayError('NOT_FOUND', 'Order not found');
      return send(res, 200, order.status === 'pending' ? withQr(order) : { order });
    }

    if (method === 'POST' && (m = /^\/orders\/([A-Za-z0-9]{1,64})\/utr$/.exec(path))) {
      const userId = await requireUser(req);
      const { utr } = await readBody(req);
      return send(res, 200, { order: await pay.submitUtr({ orderId: m[1], userId, utr: String(utr ?? '') }) });
    }

    if (method === 'GET' && path === '/admin/orders') {
      await requireAdmin(req);
      const filter = {};
      for (const k of ['status', 'userId', 'amount', 'limit']) if (query.get(k)) filter[k] = query.get(k);
      return send(res, 200, { orders: await pay.list(filter) });
    }

    if (method === 'POST' && (m = /^\/admin\/orders\/([A-Za-z0-9]{1,64})\/(approve|reject)$/.exec(path))) {
      await requireAdmin(req);
      const body = await readBody(req);
      const by = userIdOf(await getUser(req)) ?? undefined;
      const order = m[2] === 'approve'
        ? await pay.approve(m[1], { utr: body.utr || undefined, by })
        : await pay.reject(m[1], { reason: body.reason, by });
      return send(res, 200, { order });
    }

    return false;
  }

  return async function handle(req, res, next) {
    const url = new URL(req.url, 'http://x');
    let path = url.pathname;
    if (base) {
      if (path !== base && !path.startsWith(`${base}/`)) return next ? next() : send(res, 404, { error: 'NOT_FOUND' });
      path = path.slice(base.length) || '/';
    }
    path = path.replace(/\/+$/, '') || '/';
    try {
      const handled = await route(req, res, path, url.searchParams);
      if (handled === false) return next ? next() : send(res, 404, { error: 'NOT_FOUND', message: 'No such route' });
    } catch (err) {
      if (err instanceof UpiPayError) return send(res, err.status, { error: err.code, message: err.message });
      if (err instanceof RangeError && /^pure-upi:/.test(err.message)) return send(res, 400, { error: 'BAD_REQUEST', message: err.message });
      onError ? onError(err) : console.error(err);
      return send(res, 500, { error: 'INTERNAL', message: 'Something went wrong' });
    }
  };
}
