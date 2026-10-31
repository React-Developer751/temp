// UPI deep links (NPCI "upi://pay" linking spec). Browser-safe.

const VPA = /^[a-zA-Z0-9][a-zA-Z0-9._-]{0,255}@[a-zA-Z][a-zA-Z0-9.-]{1,63}$/;
const UTR = /^\d{12}$/;

/** True for a well-formed UPI ID (VPA) such as `name@okhdfcbank`. Does not check that it exists. */
export function isValidVpa(vpa) {
  return typeof vpa === 'string' && VPA.test(vpa);
}

/** True for a 12-digit UPI transaction reference (UTR / RRN), after removing spaces. */
export function isValidUtr(utr) {
  return typeof utr === 'string' && UTR.test(normalizeUtr(utr));
}

export function normalizeUtr(utr) {
  return String(utr).replace(/\s+/g, '');
}

/** Rupees (number or "99.07" string) -> integer paise. Throws on anything that isn't a positive, at most 2-decimal amount. */
export function toPaise(amount) {
  const text = typeof amount === 'number' ? String(amount) : amount;
  if (typeof text !== 'string' || !/^\d+(\.\d{1,2})?$/.test(text.trim())) {
    throw new RangeError(`pure-upi: invalid amount ${JSON.stringify(amount)} (use rupees with at most 2 decimals)`);
  }
  const [whole, frac = ''] = text.trim().split('.');
  const paise = Number(whole) * 100 + Number(frac.padEnd(2, '0'));
  if (!Number.isSafeInteger(paise) || paise <= 0) throw new RangeError(`pure-upi: amount must be greater than 0 (got ${amount})`);
  return paise;
}

/** Integer paise -> "99.07". */
export function formatPaise(paise) {
  if (!Number.isSafeInteger(paise) || paise < 0) throw new RangeError(`pure-upi: invalid paise ${paise}`);
  return `${Math.floor(paise / 100)}.${String(paise % 100).padStart(2, '0')}`;
}

// Notes show up in the payer's and payee's app; keep them short and plain.
function cleanText(value, max) {
  return String(value).replace(/[^\p{L}\p{M}\p{N} .,:_\-/#]/gu, ' ').replace(/\s+/g, ' ').trim().slice(0, max);
}

/**
 * Build a `upi://pay?...` link. Any UPI app (GPay, PhonePe, Paytm, BHIM, bank apps) opens it, or scans it as a QR.
 *
 * @param {object} p
 * @param {string} p.upiId     payee UPI ID (VPA), e.g. "shop@okaxis"
 * @param {string} p.name      payee name shown in the app
 * @param {number|string} [p.amount]  rupees; omit to let the payer type it
 * @param {string} [p.note]    transaction note (tn), max 50 chars
 * @param {string} [p.ref]     transaction reference (tr) - only for merchant UPI IDs; some apps reject it for personal IDs
 * @param {string} [p.merchantCode] merchant category code (mc) - only for merchant UPI IDs
 */
export function upiLink({ upiId, name, amount, note, ref, merchantCode } = {}) {
  if (!isValidVpa(upiId)) throw new TypeError(`pure-upi: invalid UPI ID ${JSON.stringify(upiId)}`);
  if (!name || !cleanText(name, 99)) throw new TypeError('pure-upi: payee name is required');
  const params = [['pa', upiId], ['pn', cleanText(name, 99)]];
  if (amount !== undefined && amount !== null) params.push(['am', formatPaise(toPaise(amount))]);
  params.push(['cu', 'INR']);
  if (note) params.push(['tn', cleanText(note, 50)]);
  if (ref) params.push(['tr', cleanText(ref, 35)]);
  if (merchantCode) {
    if (!/^\d{4}$/.test(String(merchantCode))) throw new TypeError('pure-upi: merchantCode must be 4 digits');
    params.push(['mc', String(merchantCode)]);
  }
  // `@` stays literal in pa: a few UPI apps fail to parse %40.
  return `upi://pay?${params.map(([k, v]) => `${k}=${k === 'pa' ? v : encodeURIComponent(v)}`).join('&')}`;
}

/** Parse a `upi://pay` link back into `{ upiId, name, amount, currency, note, ref, merchantCode }`. */
export function parseUpiLink(link) {
  const match = /^upi:\/\/pay\?(.*)$/i.exec(String(link));
  if (!match) throw new TypeError('pure-upi: not a upi://pay link');
  const q = Object.fromEntries(match[1].split('&').filter(Boolean).map((pair) => {
    const i = pair.indexOf('=');
    const key = i < 0 ? pair : pair.slice(0, i);
    const value = i < 0 ? '' : pair.slice(i + 1);
    return [key, decodeURIComponent(value.replace(/\+/g, ' '))];
  }));
  const out = { upiId: q.pa, name: q.pn, currency: q.cu };
  if (q.am !== undefined) out.amount = q.am;
  if (q.tn !== undefined) out.note = q.tn;
  if (q.tr !== undefined) out.ref = q.tr;
  if (q.mc !== undefined) out.merchantCode = q.mc;
  return out;
}
