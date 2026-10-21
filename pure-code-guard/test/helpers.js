import { scanSource } from '../src/index.js';

/** Fake credentials are assembled at runtime so this repo never contains a real-looking secret literal. */
export const fake = {
  awsKey: () => ['AKIA', 'QWERTY1234ABCDEF', '90'].join('').slice(0, 20),
  github: () => ['ghp', '_', 'aB3dE5gH7jK9mN1pQ3sT5vW7yZ9bD1fH3jL5'].join(''),
  stripe: () => ['sk', '_live_', '51HqLkPzA9bC3dE5fG7hJ9kL'].join(''),
  jwt: () => {
    const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
    return `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64({ sub: '1234567890', name: 'Jane Doe' })}.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c`;
  },
  highEntropy: () => 'q8Zr3Vn0xT7pLw2Yk5Bd9HcM4JsFu6Ge',
};

export const scan = (source, options = {}) => scanSource(source, { filename: 'app.js', ...options });
export const ids = (source, options) => scan(source, options).map((f) => f.ruleId);
export const has = (source, ruleId, options) => ids(source, options).includes(ruleId);
