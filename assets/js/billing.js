/* ============================================================
   WRENCHLINK — billing & invoicing engine
   Recurring monthly subscriptions, invoice accrual, payment state.
   Data lives on WL store (per-account): user.subscription,
   user.invoices, user.paymentMethod, plus a demo billing clock.
   ============================================================ */

const BILLING_PLANS = {
  tech:       { id: 'tech',       name: 'Solo',       audience: 'tech',     price: 9.95, blurb: 'Full technician access' },
  starter:    { id: 'starter',    name: 'Starter',    audience: 'employer', price: 99,   blurb: '2 active postings' },
  pro:        { id: 'pro',        name: 'Pro',        audience: 'employer', price: 249,  blurb: '10 active postings' },
  enterprise: { id: 'enterprise', name: 'Enterprise', audience: 'employer', price: 1200, blurb: 'Unlimited + ATS' },
};

const Billing = {
  money(n) {
    return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  fmtDate(d) {
    const x = (d instanceof Date) ? d : new Date(d);
    return x.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  },
  iso(d) { return d.toISOString().slice(0, 10); },
  addMonths(d, n) { const x = new Date(d); x.setMonth(x.getMonth() + n); return x; },

  // virtual "now" — real clock plus an optional demo offset (months)
  now() {
    const s = WL.get();
    return this.addMonths(new Date(), s.billingClockOffset || 0);
  },

  planForUser(u) {
    if (!u) return null;
    if (u.type === 'tech') return BILLING_PLANS.tech;
    const map = { Solo: 'tech', Starter: 'starter', Pro: 'pro', Enterprise: 'enterprise' };
    return BILLING_PLANS[map[u.plan]] || BILLING_PLANS.pro;
  },

  sub() {
    const u = WL.get().user;
    return u ? u.subscription : null;
  },
  invoices() {
    const u = WL.get().user;
    return (u && u.invoices) ? u.invoices : [];
  },
  paymentMethod() {
    const u = WL.get().user;
    return u ? u.paymentMethod || null : null;
  },

  // create a subscription for the logged-in member if none exists
  ensure() {
    const u = WL.get().user;
    if (!u || u.type === 'admin') return null;
    if (!u.subscription) {
      const plan = this.planForUser(u);
      const start = u.joined ? new Date(u.joined) : this.now();
      u.subscription = {
        planId: plan.id,
        planName: plan.name,
        price: plan.price,
        status: 'active',
        startDate: this.iso(start),
        anchorDay: start.getDate(),
        canceledAt: null,
      };
      u.invoices = u.invoices || [];
      WL.save();
    }
    this.accrue();
    return u.subscription;
  },

  // generate any missing monthly invoices from start through now
  accrue() {
    const u = WL.get().user;
    const sub = u && u.subscription;
    if (!sub) return;
    const now = this.now();
    const invs = u.invoices = u.invoices || [];
    let cursor = new Date(sub.startDate);
    let guard = 0;
    while (cursor <= now && guard < 240) {
      guard++;
      const key = cursor.getFullYear() + '-' + cursor.getMonth();
      const canceled = sub.status === 'canceled' && sub.canceledAt && new Date(sub.canceledAt) < cursor;
      if (!canceled && !invs.some(i => i.periodKey === key)) {
        const seq = invs.length + 1;
        const paid = !!u.paymentMethod;
        invs.push({
          id: 'WL-' + cursor.getFullYear() + '-' + String(seq).padStart(4, '0'),
          periodKey: key,
          date: this.iso(cursor),
          periodStart: this.iso(cursor),
          periodEnd: this.iso(this.addMonths(cursor, 1)),
          description: sub.planName + ' plan — monthly subscription',
          amount: sub.price,
          status: paid ? 'paid' : 'due',
          paidDate: paid ? this.iso(cursor) : null,
        });
      }
      cursor = this.addMonths(cursor, 1);
    }
    invs.sort((a, b) => b.date.localeCompare(a.date));
    WL.save();
  },

  nextBillDate() {
    const sub = this.sub();
    if (!sub || sub.status === 'canceled') return null;
    // next anchor-day boundary strictly after now
    const now = this.now();
    let d = new Date(now.getFullYear(), now.getMonth(), sub.anchorDay);
    if (d <= now) d = this.addMonths(d, 1);
    return d;
  },

  balanceDue() {
    return this.invoices().filter(i => i.status === 'due').reduce((a, i) => a + i.amount, 0);
  },

  setPaymentMethod(pm) {
    const u = WL.get().user;
    u.paymentMethod = pm;
    // auto-settle outstanding invoices on the new card
    (u.invoices || []).forEach(i => { if (i.status === 'due') { i.status = 'paid'; i.paidDate = this.iso(this.now()); } });
    WL.save();
  },

  changePlan(planId) {
    const u = WL.get().user, sub = u.subscription, p = BILLING_PLANS[planId];
    if (!sub || !p) return;
    sub.planId = p.id; sub.planName = p.name; sub.price = p.price;
    sub.status = 'active'; sub.canceledAt = null;
    if (u.type === 'employer') u.plan = p.name;
    WL.save();
  },

  cancel() {
    const sub = this.sub(); if (!sub) return;
    sub.status = 'canceled'; sub.canceledAt = this.iso(this.now());
    WL.save();
  },
  reactivate() {
    const sub = this.sub(); if (!sub) return;
    sub.status = 'active'; sub.canceledAt = null;
    this.accrue(); WL.save();
  },

  payInvoice(id) {
    const inv = this.invoices().find(i => i.id === id);
    if (inv) { inv.status = 'paid'; inv.paidDate = this.iso(this.now()); WL.save(); }
  },

  // generate a monthly invoice series for any account (used by admin oversight)
  genInvoices(opts) {
    const now = this.now();
    const out = [];
    let cursor = new Date(opts.startISO);
    let seq = 0, guard = 0;
    const hasCard = !!opts.hasCard;
    while (cursor <= now && guard < 240) {
      guard++; seq++;
      const due = opts.status === 'past_due' && cursor > this.addMonths(now, -1); // most recent unpaid if past_due
      const paid = hasCard && !due;
      out.push({
        id: 'WL-' + cursor.getFullYear() + '-' + String(seq).padStart(4, '0'),
        date: this.iso(cursor),
        periodStart: this.iso(cursor),
        periodEnd: this.iso(this.addMonths(cursor, 1)),
        description: (opts.planName || 'Subscription') + ' plan — monthly subscription',
        amount: opts.price,
        status: paid ? 'paid' : 'due',
        paidDate: paid ? this.iso(cursor) : null,
      });
      cursor = this.addMonths(cursor, 1);
    }
    out.sort((a, b) => b.date.localeCompare(a.date));
    return out;
  },

  // demo control: advance the billing clock one month and accrue
  advanceMonth() {
    const s = WL.get();
    s.billingClockOffset = (s.billingClockOffset || 0) + 1;
    WL.save();
    this.accrue();
  },
};
