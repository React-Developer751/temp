import { UpiPayError } from './errors.js';

// Store contract (all async):
//   insert(order)                         -> order
//   get(id)                               -> order | null
//   update(id, fromStatuses, patch)       -> updated order | null  (atomic: only if status is in fromStatuses;
//                                            a patch value of undefined removes the field; duplicate utr -> UTR_USED)
//   list({ status, userId, amountPaise, limit }) -> orders, newest first
//   reservedAmounts(minPaise, maxPaise, now)     -> paise of pending/submitted orders still holding an amount

const clone = (o) => (o ? structuredClone(o) : null);

/** In-memory store. Fine for tests and demos; orders are lost on restart. */
export function memoryStore() {
  const orders = new Map();
  const utrOwner = new Map();

  return {
    async insert(order) {
      if (orders.has(order.id)) throw new Error(`pure-upi: duplicate order id ${order.id}`);
      orders.set(order.id, clone(order));
      return clone(order);
    },
    async get(id) {
      return clone(orders.get(id));
    },
    async update(id, fromStatuses, patch) {
      const order = orders.get(id);
      if (!order || !fromStatuses.includes(order.status)) return null;
      if (patch.utr !== undefined && utrOwner.has(patch.utr) && utrOwner.get(patch.utr) !== id) {
        throw new UpiPayError('UTR_USED', 'This UTR has already been used for another order');
      }
      if ('utr' in patch && order.utr !== undefined) utrOwner.delete(order.utr);
      for (const [key, value] of Object.entries(patch)) {
        if (value === undefined) delete order[key];
        else order[key] = value;
      }
      if (order.utr !== undefined) utrOwner.set(order.utr, id);
      return clone(order);
    },
    async list({ status, userId, amountPaise, limit = 100 } = {}) {
      return [...orders.values()]
        .filter((o) => (status === undefined || o.status === status)
          && (userId === undefined || o.userId === userId)
          && (amountPaise === undefined || o.amountPaise === amountPaise))
        .sort((a, b) => b.createdAt - a.createdAt)
        .slice(0, limit)
        .map(clone);
    },
    async reservedAmounts(min, max, now) {
      return [...orders.values()]
        .filter((o) => o.amountPaise >= min && o.amountPaise <= max
          && (o.status === 'submitted' || (o.status === 'pending' && o.holdUntil > now)))
        .map((o) => o.amountPaise);
    },
  };
}

/**
 * MongoDB store. Pass a native driver collection, e.g.
 *   mongoStore(client.db().collection('upi_orders'))           // mongodb driver
 *   mongoStore(mongoose.connection.collection('upi_orders'))   // mongoose
 * Call `await store.init()` once at startup to create the indexes (unique UTR).
 */
export function mongoStore(collection) {
  if (!collection || typeof collection.findOneAndUpdate !== 'function') {
    throw new TypeError('pure-upi: mongoStore needs a MongoDB collection');
  }
  const toOrder = (doc) => {
    if (!doc) return null;
    const { _id, ...rest } = doc;
    for (const k of ['createdAt', 'holdUntil', 'submittedAt', 'decidedAt']) {
      if (rest[k] instanceof Date) rest[k] = rest[k].getTime();
    }
    return { id: _id, ...rest };
  };
  // driver v4/v5 return { value, ok }, v6+ returns the document
  const unwrap = (res) => (res && typeof res === 'object' && 'ok' in res && 'value' in res ? res.value : res);

  return {
    async init() {
      await collection.createIndex({ utr: 1 }, { unique: true, partialFilterExpression: { utr: { $type: 'string' } } });
      await collection.createIndex({ status: 1, createdAt: -1 });
      await collection.createIndex({ userId: 1, createdAt: -1 });
      await collection.createIndex({ amountPaise: 1, status: 1 });
    },
    async insert(order) {
      const { id, ...rest } = order;
      await collection.insertOne({ _id: id, ...rest });
      return order;
    },
    async get(id) {
      return toOrder(await collection.findOne({ _id: id }));
    },
    async update(id, fromStatuses, patch) {
      const $set = {};
      const $unset = {};
      for (const [k, v] of Object.entries(patch)) {
        if (v === undefined) $unset[k] = '';
        else $set[k] = v;
      }
      const change = {};
      if (Object.keys($set).length) change.$set = $set;
      if (Object.keys($unset).length) change.$unset = $unset;
      try {
        const res = await collection.findOneAndUpdate(
          { _id: id, status: { $in: fromStatuses } },
          change,
          { returnDocument: 'after' },
        );
        return toOrder(unwrap(res));
      } catch (err) {
        if (err?.code === 11000) throw new UpiPayError('UTR_USED', 'This UTR has already been used for another order');
        throw err;
      }
    },
    async list({ status, userId, amountPaise, limit = 100 } = {}) {
      const q = {};
      if (status !== undefined) q.status = status;
      if (userId !== undefined) q.userId = userId;
      if (amountPaise !== undefined) q.amountPaise = amountPaise;
      const docs = await collection.find(q).sort({ createdAt: -1 }).limit(limit).toArray();
      return docs.map(toOrder);
    },
    async reservedAmounts(min, max, now) {
      const docs = await collection.find(
        {
          amountPaise: { $gte: min, $lte: max },
          $or: [{ status: 'submitted' }, { status: 'pending', holdUntil: { $gt: now } }],
        },
        { projection: { amountPaise: 1 } },
      ).toArray();
      return docs.map((d) => d.amountPaise);
    },
  };
}
