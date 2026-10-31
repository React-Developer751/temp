import type { Plan, UpiOrder, ListFilter } from './index.js';

export class UpiClientError extends Error {
  readonly status: number;
  /** Server error code, e.g. 'UTR_USED', 'INVALID_UTR', 'UNAUTHORIZED'. */
  readonly code: string;
}

export interface OrderResponse {
  order: UpiOrder;
  /** upi://pay link (present while the order is pending). */
  link?: string;
  /** QR code as an SVG string (present while the order is pending). */
  qrSvg?: string;
}

export interface UpiClientOptions {
  /** Where upiHandler is mounted. Default '/api/upi'. */
  baseUrl?: string;
  /** Extra headers (e.g. Authorization), or a function returning them. */
  headers?: Record<string, string> | (() => Record<string, string> | Promise<Record<string, string>>);
  /** Default 'include' (send cookies). */
  credentials?: RequestCredentials;
  fetch?: typeof fetch;
}

export interface UpiClient {
  plans(): Promise<Plan[]>;
  createOrder(plan: string): Promise<Required<OrderResponse>>;
  getOrder(orderId: string): Promise<OrderResponse>;
  myOrders(): Promise<UpiOrder[]>;
  submitUtr(orderId: string, utr: string): Promise<UpiOrder>;
  admin: {
    list(filter?: ListFilter): Promise<UpiOrder[]>;
    approve(orderId: string, utr?: string): Promise<UpiOrder>;
    reject(orderId: string, reason?: string): Promise<UpiOrder>;
  };
}

export function createUpiClient(options?: UpiClientOptions): UpiClient;
/** True on phones/tablets, where a upi:// link can open the UPI app directly. */
export function canOpenUpiApp(userAgent?: string): boolean;
