import type { IncomingMessage, ServerResponse } from 'node:http';

// ---- QR ----

export type ErrorCorrectionLevel = 'L' | 'M' | 'Q' | 'H';

export interface QrOptions {
  /** Error correction level. Default 'M' (~15% damage tolerated). */
  ecl?: ErrorCorrectionLevel;
  minVersion?: number;
  maxVersion?: number;
  /** Force a mask pattern 0-7. Default: the best one by the spec's penalty score. */
  mask?: number;
}

export interface QrMatrix {
  version: number;
  /** Modules per side (version * 4 + 17). */
  size: number;
  ecl: ErrorCorrectionLevel;
  mask: number;
  /** modules[y][x] === true means dark. */
  modules: boolean[][];
}

export interface QrSvgOptions extends QrOptions {
  /** Quiet zone in modules. Default 4. */
  border?: number;
  dark?: string;
  light?: string;
  /** Width/height attribute in px. Default: none (scales to its container). */
  size?: number;
  /** Accessible <title>. */
  title?: string;
}

export function qrMatrix(text: string, options?: QrOptions): QrMatrix;
export function qrSvg(text: string, options?: QrSvgOptions): string;
export function qrDataUrl(text: string, options?: QrSvgOptions): string;

// ---- UPI links ----

export interface UpiLinkParams {
  /** Payee UPI ID (VPA), e.g. "shop@okaxis". */
  upiId: string;
  /** Payee name shown in the UPI app. */
  name: string;
  /** Rupees; omit to let the payer enter it. At most 2 decimals. */
  amount?: number | string;
  /** Transaction note (tn), up to 50 characters. */
  note?: string;
  /** Transaction reference (tr). Merchant UPI IDs only; some apps reject it for personal IDs. */
  ref?: string;
  /** Merchant category code (mc), 4 digits. Merchant UPI IDs only. */
  merchantCode?: string | number;
}

export interface ParsedUpiLink {
  upiId: string;
  name?: string;
  currency?: string;
  amount?: string;
  note?: string;
  ref?: string;
  merchantCode?: string;
}

export function upiLink(params: UpiLinkParams): string;
export function parseUpiLink(link: string): ParsedUpiLink;
export function isValidVpa(vpa: unknown): boolean;
/** 12-digit UPI transaction reference (spaces ignored). */
export function isValidUtr(utr: unknown): boolean;
export function normalizeUtr(utr: string): string;
/** Rupees -> integer paise. Throws RangeError for invalid amounts. */
export function toPaise(amount: number | string): number;
/** Integer paise -> "99.07". */
export function formatPaise(paise: number): string;

// ---- Orders ----

export type OrderStatus = 'pending' | 'submitted' | 'approved' | 'rejected';

export interface UpiOrder {
  id: string;
  userId: string;
  plan: string;
  /** Amount to pay, e.g. "99.07". */
  amount: string;
  amountPaise: number;
  status: OrderStatus;
  /** Epoch ms. */
  createdAt: number;
  /** Until this time (epoch ms) no other pending order gets the same amount. */
  holdUntil: number;
  utr?: string;
  submittedAt?: number;
  decidedAt?: number;
  decidedBy?: string;
  reason?: string;
  /** UTR the payer had entered, kept for reference after a rejection. */
  rejectedUtr?: string;
  meta?: unknown;
}

export interface PlanInput {
  /** Rupees. */
  price: number | string;
  name?: string;
  [extra: string]: unknown;
}

export interface Plan {
  id: string;
  name: string;
  /** "99.00" */
  price: string;
  [extra: string]: unknown;
}

export interface ListFilter {
  status?: OrderStatus;
  userId?: string;
  /** Rupees, e.g. "99.07" - find the order behind a credit you see in your bank app. */
  amount?: number | string;
  /** Default 100, max 500. */
  limit?: number | string;
}

export interface StoreFilter {
  status?: OrderStatus;
  userId?: string;
  amountPaise?: number;
  limit?: number;
}

export interface UpiStore {
  insert(order: UpiOrder): Promise<UpiOrder>;
  get(id: string): Promise<UpiOrder | null>;
  /**
   * Atomically apply `patch` only if the order's status is in `fromStatuses`; return the updated order or null.
   * A patch value of `undefined` removes the field. A duplicate `utr` must throw UpiPayError('UTR_USED').
   */
  update(id: string, fromStatuses: OrderStatus[], patch: Partial<Record<keyof UpiOrder, unknown>>): Promise<UpiOrder | null>;
  list(filter: StoreFilter): Promise<UpiOrder[]>;
  reservedAmounts(minPaise: number, maxPaise: number, now: number): Promise<number[]>;
}

export function memoryStore(): UpiStore;
export function mongoStore(collection: unknown): UpiStore & { init(): Promise<void> };

export interface UpiPayOptions {
  /** Your UPI ID (VPA). A merchant/business UPI ID is recommended. */
  upiId: string;
  /** Payee name shown in the UPI app. */
  name: string;
  /** e.g. { monthly: { price: 99, name: 'Monthly' }, yearly: 799 } */
  plans: Record<string, PlanInput | number | string>;
  /** Default memoryStore() (lost on restart). */
  store?: UpiStore;
  /** Add 1-99 paise so each pending order has a distinct amount. Default true. */
  uniqueAmount?: boolean;
  /** How long a pending order keeps its unique amount, ms. Default 30 minutes. */
  holdMs?: number;
  /** Note shown in the UPI app: "<notePrefix> <orderId>". Default "Order". */
  notePrefix?: string;
  onSubmitted?: (order: UpiOrder) => unknown;
  /** Grant the purchase here. If it throws, the approval is rolled back. */
  onApproved?: (order: UpiOrder) => unknown;
  onRejected?: (order: UpiOrder) => unknown;
  /** Clock, for tests. */
  now?: () => number;
}

export interface UpiPay {
  readonly upiId: string;
  readonly name: string;
  readonly store: UpiStore;
  plans(): Plan[];
  linkFor(order: UpiOrder): string;
  qrFor(order: UpiOrder, options?: QrSvgOptions): string;
  createOrder(input: { userId: string | number; plan: string; meta?: unknown }): Promise<{ order: UpiOrder; link: string }>;
  getOrder(orderId: string): Promise<UpiOrder>;
  submitUtr(input: { orderId: string; userId?: string | number; utr: string }): Promise<UpiOrder>;
  approve(orderId: string, options?: { utr?: string; by?: string }): Promise<UpiOrder>;
  reject(orderId: string, options?: { reason?: string; by?: string }): Promise<UpiOrder>;
  list(filter?: ListFilter): Promise<UpiOrder[]>;
}

export function createUpiPay(options: UpiPayOptions): UpiPay;

export type UpiErrorCode =
  | 'INVALID_PLAN' | 'INVALID_UTR' | 'BAD_REQUEST' | 'UNAUTHORIZED' | 'FORBIDDEN' | 'NOT_FOUND' | 'BAD_STATE' | 'UTR_USED';

export class UpiPayError extends Error {
  constructor(code: UpiErrorCode, message: string);
  readonly code: UpiErrorCode;
  /** HTTP status for this error. */
  readonly status: number;
}

// ---- HTTP ----

export interface UpiHandlerOptions<Req = IncomingMessage> {
  /** Logged-in user's id (or an object with id / _id), or null/undefined when logged out. */
  getUser(req: Req): unknown;
  /** True if this request may list/approve/reject orders. */
  isAdmin(req: Req): boolean | Promise<boolean>;
  /** Path prefix to strip when not mounted with app.use(path, ...), e.g. '/api/upi'. */
  basePath?: string;
  /** Include qrSvg in order responses. Default true. */
  qr?: boolean;
  /** Called for unexpected (500) errors. Default console.error. */
  onError?: (error: unknown) => void;
}

export function upiHandler<Req extends IncomingMessage = IncomingMessage>(
  pay: UpiPay,
  options: UpiHandlerOptions<Req>,
): (req: Req, res: ServerResponse, next?: (err?: unknown) => void) => Promise<void>;
