# WrenchLink

**Where Automotive Talent Meets Opportunity** — a job platform for auto repair & auto body technicians and the shops that hire them. An Indeed alternative built specifically for the trade.

## Run it locally

**Node** (same as production):

```
npm start
```

…then open **http://localhost:8080**.

Or with Python: `python -m http.server 8080`. Or double-click **`START-WRENCHLINK.bat`** on Windows.

> 100% static front end (HTML/CSS/JS). Accounts, jobs, applications, subscriptions, and invoices are stored in your browser's `localStorage`, so it's fully interactive with no database. Clearing site data resets the demo.

## Deploy on Railway

The repo is Railway-ready:

- `package.json` → `npm start` runs `server.js` (a zero-dependency Node static server that binds `process.env.PORT`).
- `Procfile` → `web: npm start`.

On Railway: **New Project → Deploy from GitHub → chrispeer69/Wrenchlink**. Nixpacks detects Node and runs `npm start` automatically. No build step or env vars required.

## Pages

| Page | File | What it does |
|------|------|--------------|
| Landing | `index.html` | Hero, how-it-works, live job preview, features, sign-up |
| Find Jobs | `jobs.html` | Search/filter listings by city pool, type, pay, schedule; 1-click apply & save |
| My Vault (Employee) | `vault.html` | Full technician profile: profile & skills, contact & availability, certifications, work history, education, references, documents, applications, saved jobs — with a completeness meter |
| Employer Dashboard | `employer.html` | Business profile + description + perks, post & manage jobs, search talent, applicants |
| Billing & Invoices | `billing.html` | Subscription, payment method, recurring monthly invoices (view/print), plan changes, cancel |
| Admin Console | `admin.html` | Manage all employers & technicians, subscriptions/billing, MRR, city-pool activity |
| City Pools | `city-pools.html` | Browse metro talent markets by region |
| Pricing | `pricing.html` | Technician Solo $9.95/mo; employer Starter/Pro/Enterprise |
| Legal | `legal.html` | Terms, Privacy, Cookies, Acceptable Use, Billing & Refunds, Disclaimers |

## Billing model

- **Technicians** — Solo plan, **$9.95/mo**.
- **Employers** — Starter $99, Pro $249, Enterprise custom, per month.
- Recurring engine (`assets/js/billing.js`) accrues one invoice per month from signup, auto-settles on a saved card, supports plan change / cancel / reactivate, and a "Advance billing month" demo control to watch recurring charges accrue. Invoices are printable (Print / Save PDF).

## Demo logins (any password)

- **Technician** — *Get Started → Tech* (or Sign In as Technician) → lands in **My Vault**.
- **Employer** — *Get Started → Employer* → **Employer Dashboard**.
- **Admin** — Sign In with **`admin@wrenchlink.io`** → **Admin Console**.

## Structure

```
site/
  index.html jobs.html vault.html employer.html billing.html
  admin.html city-pools.html pricing.html legal.html
  server.js package.json Procfile        # Railway / Node hosting
  assets/
    css/styles.css     design system (light + navy, Inter)
    js/icons.js        inline SVG icon set
    js/data.js         seed jobs/candidates/cities + localStorage store
    js/billing.js      subscriptions + recurring invoicing engine
    js/app.js          nav, auth modal, toast, cookie consent, route guards
    js/footer.js       shared footer
    img/favicon.ico
```

> The legal documents are a template framework and should be reviewed by a licensed attorney before public launch.
