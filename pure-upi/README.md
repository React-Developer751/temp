# pure-upi

Zero-dependency UPI payments for your own website (Node.js >= 20.19). It takes money straight into **your UPI ID**:
no payment gateway, no company registration and no gateway fees. Each developer sets their own UPI ID (`upiId`),
and the library takes no cut. See [Limits, costs and checks](#limits-costs-and-checks) before going live.

- `upi://pay` links that open GPay, PhonePe, Paytm, BHIM and bank apps
- A **built-in QR code generator** (ISO 18004, versions 1-40, no `qrcode` package needed)
- Orders with **unique amounts** (₹99.07, ₹99.13, ...) so you can tell payments apart in your bank app
- **UTR verification**: the payer enters the 12-digit UPI reference and you approve it; each UTR can be used only once
- A ready-made **Express / Node `http` handler**, a **browser client**, and stores for **MongoDB / Mongoose** and memory

```
buyer clicks "Buy" -> QR / "Open UPI app" for ₹99.07 -> pays in any UPI app
   -> enters the UTR -> you see ₹99.07 + that UTR in your bank app -> Approve -> onApproved() grants premium
```

> **How verification works.** A plain UPI ID has no API that tells your server "payment received".
> You approve each payment after you see it in your bank or UPI app. For automatic confirmation you need a
> payment gateway (Razorpay, Cashfree...). See [Limits, costs and checks](#limits-costs-and-checks).

## Install

```bash
npm i pure-upi
```

## MERN in 3 steps

**1. Backend (Express + Mongoose)**

```js
import { createUpiPay, mongoStore, upiHandler } from 'pure-upi';

const store = mongoStore(mongoose.connection.collection('upi_orders'));
await store.init(); // creates indexes (unique UTR)

const pay = createUpiPay({
  upiId: process.env.UPI_ID,          // yourname@okaxis
  name: 'My Site',
  plans: { monthly: { price: 99, name: 'Premium - 1 month' }, yearly: { price: 799 } },
  store,
  onApproved: (order) => User.updateOne({ _id: order.userId }, { premium: true }),
});

app.use(express.json());
app.use('/api/upi', requireLogin, upiHandler(pay, {
  getUser: (req) => req.user,                    // { _id } / { id } / id string
  isAdmin: (req) => req.user?.role === 'admin',
}));
```

**2. Frontend (React)**: copy [`examples/react/UpiCheckout.jsx`](examples/react/UpiCheckout.jsx), then:

```jsx
<UpiCheckout plan="monthly" onPaid={refetchUser} />
```

**3. Admin**: copy [`examples/admin.html`](examples/admin.html) (or build your own with `client.admin.*`). It lists
submitted payments. Check your bank app, then Approve or Reject.

Full working demo (no dependencies, no database):

```bash
UPI_ID=yourname@okaxis node examples/server.js
# buyer: http://localhost:3000    admin: http://localhost:3000/admin.html (log in as "admin")
```

## HTTP API (`upiHandler`)

| Method & path | Who | Body / query | Returns |
|---|---|---|---|
| `GET /plans` | anyone | | `{ plans }` |
| `POST /orders` | user | `{ plan }` | `{ order, link, qrSvg }` |
| `GET /orders` | user | | `{ orders }` (own, newest first) |
| `GET /orders/:id` | owner / admin | | `{ order, link?, qrSvg? }` (QR only while pending) |
| `POST /orders/:id/utr` | owner | `{ utr }` | `{ order }` |
| `GET /admin/orders` | admin | `?status=&amount=&userId=&limit=` | `{ orders }` |
| `POST /admin/orders/:id/approve` | admin | `{ utr? }` | `{ order }` |
| `POST /admin/orders/:id/reject` | admin | `{ reason? }` | `{ order }` |

Errors are `{ error, message }` with status 400 `INVALID_PLAN` / `INVALID_UTR` / `BAD_REQUEST`, 401 `UNAUTHORIZED`,
403 `FORBIDDEN`, 404 `NOT_FOUND`, 409 `BAD_STATE` / `UTR_USED`. Unknown routes call `next()` (Express) or return 404.
Mounted without `app.use(path, ...)`, pass `basePath: '/api/upi'`. Reads JSON itself if no body parser ran.

## Browser client: `pure-upi/client`

Works with React, Vue, Svelte or plain JS.

```js
import { createUpiClient, canOpenUpiApp } from 'pure-upi/client';
const upi = createUpiClient({ baseUrl: '/api/upi', headers: () => ({ Authorization: `Bearer ${token}` }) });

const { order, link, qrSvg } = await upi.createOrder('monthly');
await upi.submitUtr(order.id, '412345678901');
(await upi.getOrder(order.id)).order.status; // 'pending' | 'submitted' | 'approved' | 'rejected'

await upi.admin.list({ status: 'submitted' });
await upi.admin.approve(order.id);
await upi.admin.reject(order.id, 'Payment not received');
```

Failed calls throw `UpiClientError` with `.status` and `.code`. `canOpenUpiApp()` is true on phones, where the
`link` opens the UPI app directly. On desktop, show the QR.

## `createUpiPay(options)`

| Option | Default | |
|---|---|---|
| `upiId` | required | Your UPI ID. Only the format is checked; send yourself a ₹1 test first. A business/merchant UPI ID is best (see [Limits](#limits-costs-and-checks)) |
| `name` | required | Payee name shown in the app |
| `plans` | required | `{ id: { price, name?, ...anything } }` or `{ id: price }`, rupees |
| `store` | `memoryStore()` | `mongoStore(collection)` or your own (see `UpiStore` in the types) |
| `uniqueAmount` | `true` | Add 1-99 paise so each pending order has a different amount. The **payer** pays this extra (₹99 becomes ₹99.37); `false` charges the exact price |
| `holdMs` | 30 min | How long a pending order keeps its amount reserved |
| `notePrefix` | `'Order'` | UPI note: `"<prefix> <orderId>"` |
| `onSubmitted(order)` | | e.g. email/Telegram yourself that a payment is waiting |
| `onApproved(order)` | | Grant the purchase. If it throws, the approval is rolled back |
| `onRejected(order)` | | |

Methods: `plans()`, `createOrder({ userId, plan, meta? })`, `getOrder(id)`, `submitUtr({ orderId, userId?, utr })`,
`approve(id, { utr?, by? })`, `reject(id, { reason?, by? })`, `list({ status?, userId?, amount?, limit? })`,
`linkFor(order)`, `qrFor(order, svgOptions?)`.

Guarantees: amounts are integer paise (no float errors). A UTR can be attached to only one order (unique index in
MongoDB). Rejecting frees the UTR again. State changes are atomic (`pending -> submitted -> approved|rejected`), so
two admins clicking Approve at once run `onApproved` only once.

## Building blocks

Each one works on its own, also in the browser.

```js
import { upiLink, parseUpiLink, isValidVpa, isValidUtr } from 'pure-upi/link';
import { qrSvg, qrDataUrl, qrMatrix } from 'pure-upi/qr';

const link = upiLink({ upiId: 'shop@okaxis', name: 'My Shop', amount: 249, note: 'Invoice 17' });
// upi://pay?pa=shop@okaxis&pn=My%20Shop&am=249.00&cu=INR&tn=Invoice%2017

qrSvg(link, { size: 240 });          // <svg ...> string
qrDataUrl(link);                     // for <img src>
qrMatrix('any text', { ecl: 'H' });  // { version, size, modules[y][x] } - draw it yourself
```

A static QR for a shop counter: `qrSvg(upiLink({ upiId, name }))` (no amount, so the payer types it).

## Limits, costs and checks

These come from UPI, banks and the law, not from the library. Rules and fees change, so check the current ones
with your bank or UPI app before going live.

**Before going live**

- **Send yourself ₹1 first.** `upiId` is checked only for format (`name@bank`). It cannot check that the ID exists
  or that it is yours. A typo means failed payments, or money going to someone else's ID. Run the demo with your ID
  (`UPI_ID=you@bank node examples/server.js`), pay ₹1 from another app or account, and check your bank statement.
- **Use a business UPI ID.** Many incoming payments to a personal UPI ID can get it flagged, and some apps limit
  `upi://` links to personal IDs (they may refuse "Open UPI app"; scanning the QR usually still works).
  A free merchant UPI ID from PhonePe Business, Paytm for Business, BharatPe or your bank needs only PAN + bank KYC
  and gives instant payment alerts.

**Verification**

- **Manual approval.** Never approve without seeing the money in your bank or UPI app: anyone can type a fake UTR.
  Look up the order by its unique amount (`?amount=99.07` / admin page search) and compare the UTR.
- **No automatic confirmation.** When you need it, a gateway such as Razorpay or Cashfree accepts individuals
  (PAN + bank account + Terms/Privacy/Refund/Contact pages). Keep `pure-upi` for the UI and plug the gateway in later.

**Costs**

- **The library charges nothing.** Money goes from the payer's UPI app straight to your UPI ID, with no server or
  company in between.
- **UPI from a bank account: ₹0** for you and the payer (zero MDR), to personal and merchant UPI IDs. This is how
  most people pay.
- **Wallet balance (PPI) over ₹2,000 to a merchant UPI ID:** the merchant may pay an interchange fee of up to about 1.1%.
- **RuPay credit card linked to UPI, paying a merchant UPI ID:** a merchant fee (MDR) can apply.
- **Merchant apps** (PhonePe Business, Paytm for Business, BharatPe) are free for bank-account UPI, but extras such as
  soundbox rent or instant settlement may cost money. Read their fee list when you sign up.
- **Unique amounts are paid by the buyer.** With `uniqueAmount: true` (default) the buyer pays 1-99 paise extra
  (₹99 becomes ₹99.37). Nothing is deducted from you. Set `uniqueAmount: false` to charge the exact price. Payments
  are then matched only by UTR, so check the UTR in your bank app carefully.

**Limits**

- **Per-payment limit:** most banks allow up to ₹1,00,000 per UPI payment and set a daily limit (some categories
  allow more). Payers with lower limits, such as new UPI users in their first 24 hours, may see a failure for
  larger amounts. Keep plan prices well below these limits.
- **Refunds are manual.** A UPI payment cannot be reversed from your website. To refund, send the money back from
  your UPI app and `reject()` or mark the order in your own records.

**Legal and tax**

- **Your own sales only.** Collecting money for other businesses and passing it on needs an RBI payment
  aggregator licence. This library is for selling your own products.
- **Tax.** Sales income must be shown in your income tax return. GST registration becomes required once turnover
  crosses the GST threshold (about ₹20 lakh a year for services, lower in some states), and some online services
  may need it earlier. Ask a CA if unsure.

## License

MIT
