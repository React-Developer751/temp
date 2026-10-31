// MERN backend example (Express + Mongoose). Copy into your project:
//   npm i pure-upi
// Your app already has express, mongoose and some auth middleware; pure-upi itself adds no dependencies.

import express from 'express';
import mongoose from 'mongoose';
import { createUpiPay, mongoStore, upiHandler } from 'pure-upi';
import User from './models/User.js';           // your model
import { requireLogin } from './middleware/auth.js'; // sets req.user (JWT / session)

await mongoose.connect(process.env.MONGO_URL);

const store = mongoStore(mongoose.connection.collection('upi_orders'));
await store.init(); // indexes, incl. unique UTR

const pay = createUpiPay({
  upiId: process.env.UPI_ID,          // e.g. yourname@okaxis (a business/merchant UPI ID is best)
  name: 'My Site',
  plans: {
    monthly: { price: 99, name: 'Premium - 1 month', days: 30 },
    yearly: { price: 799, name: 'Premium - 1 year', days: 365 },
  },
  store,
  notePrefix: 'Premium',
  onApproved: async (order) => {
    const days = order.plan === 'yearly' ? 365 : 30;
    await User.updateOne(
      { _id: order.userId },
      { premium: true, premiumUntil: new Date(Date.now() + days * 864e5) },
    );
  },
});

const app = express();
app.use(express.json());
app.use('/api/upi', requireLogin, upiHandler(pay, {
  getUser: (req) => req.user,                 // { _id } or { id } works
  isAdmin: (req) => req.user?.role === 'admin',
}));

app.listen(5000);
