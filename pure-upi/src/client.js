// Browser client for upiHandler. No framework needed; works with React, Vue, Svelte or plain JS.

export class UpiClientError extends Error {
  constructor(status, code, message) {
    super(message);
    this.name = 'UpiClientError';
    this.status = status;
    this.code = code;
  }
}

export function createUpiClient({ baseUrl = '/api/upi', headers = {}, credentials = 'include', fetch: fetchFn = globalThis.fetch } = {}) {
  const base = baseUrl.replace(/\/+$/, '');

  async function call(method, path, body) {
    const extra = typeof headers === 'function' ? await headers() : headers;
    const res = await fetchFn(`${base}${path}`, {
      method,
      credentials,
      headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...extra },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new UpiClientError(res.status, data.error ?? 'HTTP_ERROR', data.message ?? `HTTP ${res.status}`);
    return data;
  }
  const id = (orderId) => encodeURIComponent(orderId);

  return {
    plans: async () => (await call('GET', '/plans')).plans,
    /** -> { order, link, qrSvg } */
    createOrder: (plan) => call('POST', '/orders', { plan }),
    getOrder: (orderId) => call('GET', `/orders/${id(orderId)}`),
    myOrders: async () => (await call('GET', '/orders')).orders,
    submitUtr: async (orderId, utr) => (await call('POST', `/orders/${id(orderId)}/utr`, { utr })).order,
    admin: {
      list: async (filter = {}) => {
        const q = new URLSearchParams(Object.entries(filter).filter(([, v]) => v !== undefined && v !== '')).toString();
        return (await call('GET', `/admin/orders${q ? `?${q}` : ''}`)).orders;
      },
      approve: async (orderId, utr) => (await call('POST', `/admin/orders/${id(orderId)}/approve`, utr ? { utr } : {})).order,
      reject: async (orderId, reason) => (await call('POST', `/admin/orders/${id(orderId)}/reject`, reason ? { reason } : {})).order,
    },
  };
}

/** True on phones/tablets, where a upi:// link can open the UPI app directly (desktop users scan the QR). */
export function canOpenUpiApp(userAgent = globalThis.navigator?.userAgent ?? '') {
  return /Android|iPhone|iPad|iPod/i.test(userAgent);
}
