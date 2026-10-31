# Changelog

## 0.1.0
- `createOrder` returns the user's open order for the same plan while its hold lasts (no order spam).
- `holdMs` and `qrSvg({ size })` are validated; plan ids such as `__proto__` work.
- Reed-Solomon helpers are internal (not exported from `pure-upi/qr`).
- Demo server answers 400 to invalid JSON instead of crashing; Express example uses `PORT` (default 4000).
- First release: `upiLink` / `parseUpiLink`, zero-dependency QR encoder (`qrMatrix`, `qrSvg`, `qrDataUrl`),
  `createUpiPay` orders with unique amounts and UTR flow, `upiHandler` for Express / Node `http`,
  `memoryStore` and `mongoStore`, browser client `pure-upi/client`.
