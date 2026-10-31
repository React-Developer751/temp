const STATUS = {
  INVALID_PLAN: 400,
  INVALID_UTR: 400,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  BAD_STATE: 409,
  UTR_USED: 409,
};

export class UpiPayError extends Error {
  /**
   * @param {keyof typeof STATUS} code
   * @param {string} message
   */
  constructor(code, message) {
    super(message);
    this.name = 'UpiPayError';
    this.code = code;
    this.status = STATUS[code] ?? 500;
  }
}
