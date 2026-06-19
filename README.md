# WrenchLink

**Where Automotive Talent Meets Opportunity** — a job platform for auto repair & auto body technicians and the shops that hire them. An Indeed alternative built specifically for the trade.

## Run it locally

Double-click **`START-WRENCHLINK.bat`** (it starts a local server and opens the site).

Or manually, from this folder:

```
python -m http.server 8080
```

Then visit **http://127.0.0.1:8080/index.html**

> The site is 100% static (HTML/CSS/JS). All accounts, jobs, applications, and admin actions are stored in your browser's `localStorage`, so it's fully interactive with no backend required. Clearing site data resets the demo.

## Pages

| Page | File | What it does |
|------|------|--------------|
| Landing | `index.html` | Hero, how-it-works, live job preview, features, sign-up |
| Find Jobs | `jobs.html` | Search/filter listings by city pool, type, pay, schedule; 1-click apply & save |
| My Vault (Employee) | `vault.html` | Full technician profile: skills, certifications, work history, salary target, availability, applications & saved jobs — all editable & saved |
| Employer Dashboard | `employer.html` | Business profile + description + perks, post & manage jobs, search talent, view applicants |
| Admin Console | `admin.html` | Master back end: manage all employers & technicians, subscriptions/billing, MRR, city-pool activity |
| City Pools | `city-pools.html` | Browse metro talent markets by region |
| Pricing | `pricing.html` | Employer plans (Starter/Pro/Enterprise); technicians always free |

## Demo logins

- **Technician** — click *Get Started → Tech*, or *Sign In* with role "Technician" (any email/password). Lands in **My Vault**.
- **Employer** — *Get Started → Employer*, or *Sign In* with role "Employer". Lands in the **Employer Dashboard**.
- **Admin** — *Sign In* with email **`admin@wrenchlink.io`** (any password). Lands in the **Admin Console**. (Also reachable from the footer "Admin" link.)

## Structure

```
site/
  index.html  jobs.html  vault.html  employer.html  admin.html
  city-pools.html  pricing.html
  assets/
    css/styles.css      design system + all components
    js/data.js          seed jobs/candidates/cities + localStorage store
    js/app.js           nav, auth modal, toast, route guards
    js/footer.js        shared footer
    img/favicon.ico
```
