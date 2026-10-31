import { UpiPayError } from './errors.js';
import { formatPaise, isValidUtr, isValidVpa, normalizeUtr, toPaise, upiLink } from './link.js';
import { qrSvg } from './qr.js';
import { memoryStore } from './stores.js';

const ID_ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'; // Crockford base32: no I, L, O, U

function newId(length = 10) {
  const bytes = globalThis.crypto.getRandomValues(new Uint8Array(length));
  let id = '';
  for (const b of bytes) id += ID_ALPHABET[b & 31];
  return id;
}

function normalizePlans(plans) {
  if (!plans || typeof plans !== 'object' || !Object.keys(plans).length) {
    throw new TypeError('pure-upi: `plans` is required, e.g. { monthly: { price: 99 } }');
  }
  const out = {};
  for (const [id, plan] of Object.entries(plans)) {
    const p = typeof plan === 'object' && plan !== null ? plan : { price: plan };
    out[id] = { ...p, id, name: p.name ?? id, pricePaise: toPaise(p.price), price: formatPaise(toPaise(p.price)) };
  }
  return out;
}

/**
 * Create a UPI payment manager: orders with (optionally) unique amounts, UTR submission, admin approve/reject.
 */
export function createUpiPay({
  upiId,
  name,
  plans,
  store = memoryStore(),
  uniqueAmount = true,
  holdMs = 30 * 60 * 1000,
  notePrefix = 'Order',
  onSubmitted,
  onApproved,
  onRejected,
  now = Date.now,
} = {}) {
  if (!isValidVpa(upiId)) throw new TypeError(`pure-upi: invalid upiId ${JSON.stringify(upiId)}`);
  if (!name) throw new TypeError('pure-upi: `name` (payee name) is required');
  const planMap = normalizePlans(plans);

  const linkFor = (order) => upiLink({ upiId, name, amount: order.amount, note: `${notePrefix} ${order.id}` });

  async function pickAmount(base) {
    if (!uniqueAmount) return base;
    const taken = new Set(await store.reservedAmounts(base + 1, base + 99, now()));
    const free = [];
    for (let p = 1; p <= 99; p++) if (!taken.has(base + p)) free.push(base + p);
    // All 99 slots busy: reuse one. The UTR still identifies the payment.
    const pool = free.length ? free : Array.from({ length: 99 }, (_, i) => base + i + 1);
    return pool[globalThis.crypto.getRandomValues(new Uint32Array(1))[0] % pool.length];
  }

  async function mustGet(orderId) {
    const order = typeof orderId === 'string' ? await store.get(orderId) : null;
    if (!order) throw new UpiPayError('NOT_FOUND', 'Order not found');
    return order;
  }

  const pay = {
    upiId,
    name,
    store,

    plans() {
      return Object.values(planMap).map(({ pricePaise, ...p }) => p);
    },

    linkFor,

    /** QR (SVG string) for an order's payment link. */
    qrFor(order, options) {
      return qrSvg(linkFor(order), { title: `Pay ₹${order.amount} to ${name}`, ...options });
    },

    async createOrder({ userId, plan, meta } = {}) {
      if (userId === undefined || userId === null || userId === '') throw new UpiPayError('UNAUTHORIZED', 'userId is required');
      const p = Object.hasOwn(planMap, plan) ? planMap[plan] : null;
      if (!p) throw new UpiPayError('INVALID_PLAN', `Unknown plan ${JSON.stringify(plan)}`);
      const amountPaise = await pickAmount(p.pricePaise);
      const t = now();
      const order = {
        id: newId(),
        userId: String(userId),
        plan: p.id,
        amountPaise,
        amount: formatPaise(amountPaise),
        status: 'pending',
        createdAt: t,
        holdUntil: t + holdMs,
      };
      if (meta !== undefined) order.meta = meta;
      await store.insert(order);
      return { order, link: linkFor(order) };
    },

    async getOrder(orderId) {
      return mustGet(orderId);
    },

    /** The payer reports the 12-digit UTR shown in their UPI app after paying. */
    async submitUtr({ orderId, userId, utr } = {}) {
      if (!isValidUtr(utr)) throw new UpiPayError('INVALID_UTR', 'UTR must be the 12-digit UPI transaction ID');
      const order = await mustGet(orderId);
      if (userId !== undefined && order.userId !== String(userId)) throw new UpiPayError('NOT_FOUND', 'Order not found');
      const updated = await store.update(order.id, ['pending'], {
        status: 'submitted',
        utr: normalizeUtr(utr),
        submittedAt: now(),
      });
      if (!updated) throw new UpiPayError('BAD_STATE', `Order is already ${order.status}`);
      await onSubmitted?.(updated);
      return updated;
    },

    /**
     * Mark an order paid after you have seen the money in your bank / UPI app. Runs `onApproved(order)`;
     * if that throws, the order goes back to its previous state so you can retry.
     */
    async approve(orderId, { utr, by } = {}) {
      const order = await mustGet(orderId);
      if (utr !== undefined && !isValidUtr(utr)) throw new UpiPayError('INVALID_UTR', 'UTR must be the 12-digit UPI transaction ID');
      const patch = { status: 'approved', decidedAt: now() };
      if (utr !== undefined) patch.utr = normalizeUtr(utr);
      if (by !== undefined) patch.decidedBy = String(by);
      const updated = await store.update(order.id, ['pending', 'submitted'], patch);
      if (!updated) throw new UpiPayError('BAD_STATE', `Order is already ${order.status}`);
      try {
        await onApproved?.(updated);
      } catch (err) {
        await store.update(order.id, ['approved'], {
          status: order.status, decidedAt: undefined, decidedBy: undefined, utr: order.utr,
        });
        throw err;
      }
      return updated;
    },

    /** Reject (payment not found, wrong amount...). The UTR is freed so the real owner can still use it. */
    async reject(orderId, { reason, by } = {}) {
      const order = await mustGet(orderId);
      const patch = { status: 'rejected', decidedAt: now(), utr: undefined };
      if (order.utr !== undefined) patch.rejectedUtr = order.utr;
      if (reason !== undefined) patch.reason = String(reason).slice(0, 500);
      if (by !== undefined) patch.decidedBy = String(by);
      const updated = await store.update(order.id, ['pending', 'submitted'], patch);
      if (!updated) throw new UpiPayError('BAD_STATE', `Order is already ${order.status}`);
      await onRejected?.(updated);
      return updated;
    },

    /** List orders. `amount` (rupees, e.g. "99.07") finds the order behind a credit in your bank app. */
    async list({ status, userId, amount, limit = 100 } = {}) {
      const filter = { limit: Math.min(Math.max(Number(limit) || 100, 1), 500) };
      if (status !== undefined) filter.status = status;
      if (userId !== undefined) filter.userId = String(userId);
      if (amount !== undefined) filter.amountPaise = toPaise(amount);
      return store.list(filter);
    },
  };
  return pay;
}
