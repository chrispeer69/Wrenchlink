# WrenchLink

WrenchLink is a Django marketplace connecting automotive technicians with repair shops, collision centers, dealerships and fleet employers.

The Django application preserves the original WrenchLink HTML/CSS design while replacing browser-only demo storage with real authentication, PostgreSQL-backed records, protected uploads and Stripe billing records.

## Current architecture

- Django 5.2
- PostgreSQL in Railway environments
- SQLite for optional local development
- Django authentication with technician/employer roles
- Email verification and password reset through SMTP
- Django administration at an environment-defined private URL
- WhiteNoise for static assets
- Stripe Checkout, Customer Portal and signed webhooks
- Technician Vault CRUD for credentials, education, work history, references and documents
- Employer job CRUD, technician search, invitations and application pipeline
- Application messaging, offers, hiring responses, reviews and notifications
- Private permission-checked document downloads
- Separate staging and production databases

The database starts empty. Demo data is added only when the optional local/staging
seed command is run manually.

## Local setup

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set local values. The checked-out `.env` is ignored by Git.

Run:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
python manage.py runserver
```

Open `http://localhost:8000`.

`seed_demo_data` is optional and intended only for local/staging layout checks. It
creates the original WrenchLink-style cities, jobs, shops and technicians and is
safe to run repeatedly. It refuses to run when `DJANGO_DEBUG=False`.

Demo logins:

```text
Technician: marcus@demo.wrenchlink.io / WrenchLinkDemo!2026
Employer: hiring@apex.demo.io / WrenchLinkDemo!2026
```

The command does not modify or replace your superuser.

The administration URL is the value of `DJANGO_ADMIN_URL`, for example:

```text
http://localhost:8000/change-this-private-admin-path/
```

Use a long random value in staging and production. Do not use `/admin/`.

## Railway environments

Create two Railway environments from the same repository:

- `staging`: separate PostgreSQL, Stripe test keys, test mail/storage configuration
- `production`: separate PostgreSQL, Stripe live keys, production mail/storage configuration

Each environment must reference its own PostgreSQL service:

```text
USE_POSTGRES=True
DB_NAME=${{Postgres.PGDATABASE}}
DB_USER=${{Postgres.PGUSER}}
DB_PASSWORD=${{Postgres.PGPASSWORD}}
DB_HOST=${{Postgres.PGHOST}}
DB_PORT=${{Postgres.PGPORT}}
```

Required application variables:

```text
DJANGO_SECRET_KEY=<unique per environment>
DJANGO_DEBUG=False
DJANGO_ADMIN_URL=<long random path unique per environment>
DJANGO_ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}},wrenchlink.online,www.wrenchlink.online
DJANGO_CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}},https://wrenchlink.online,https://www.wrenchlink.online
DJANGO_SECURE_SSL_REDIRECT=True
```

For staging, use its Railway domain and optional staging subdomain instead:

```text
DJANGO_ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}},staging.wrenchlink.online
DJANGO_CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}},https://staging.wrenchlink.online
```

Mail variables:

```text
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
```

Private document storage without AWS:

```text
RAILWAY_VOLUME_MOUNT_PATH=/data  # automatically supplied by Railway
```

Attach a separate Railway Volume to each environment and mount it at `/data`.
WrenchLink will store files under `/data/media`; you do not need to define
`MEDIA_ROOT` unless you want to override that location.
Railway's normal service filesystem is ephemeral and must not hold production
documents. The application never exposes `MEDIA_ROOT` as a public URL; downloads
pass through authenticated ownership and approval checks.

S3-compatible private storage remains optional later through the `AWS_*` variables
in `.env.example`.

Stripe variables:

```text
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_TECH_PRICE_ID=
STRIPE_STARTER_PRICE_ID=
STRIPE_PRO_PRICE_ID=
```

Configure the Stripe webhook endpoint as:

```text
https://<domain>/billing/webhook/
```

Subscribe it to customer subscription and invoice events.

Railway runs:

- build: `python manage.py collectstatic --noinput`
- pre-deploy: `python manage.py migrate --noinput`
- start: Gunicorn

Neither staging nor production is automatically seeded. Create the first administrator with:

```bash
python manage.py createsuperuser
```

Run that command separately against each environment where an administrator is required.

### Recommended Railway topology

This repository is a Django monorepo. For each Railway environment, create:

1. `WrenchLink Web` — GitHub-connected Django service; the only public service.
2. `Postgres` — private PostgreSQL database service.
3. `WrenchLink Media` — volume attached to the web service at `/data`.

No React service, Redis, Celery worker, cron service, or Dockerfile is required
for the current application. Email delivery is synchronous through SMTP.

Create `production` first, then use Railway's **Duplicate Environment** action to
create `staging`. Replace all secrets, database references, domains, Stripe keys,
and mail credentials in staging so the environments remain isolated.

For staging only, run:

```bash
python manage.py seed_demo_data --force
```

Do not run that command in production. Production starts with an empty application
database after migrations.

### GoDaddy domain

The production domain is `wrenchlink.online`. Add `www.wrenchlink.online` as the
Railway custom domain and copy Railway's generated CNAME and TXT verification
records into GoDaddy DNS exactly.

GoDaddy does not support the dynamic apex CNAME/ALIAS behavior Railway requires
for a root domain. Use either:

- GoDaddy domain forwarding from `wrenchlink.online` to
  `https://www.wrenchlink.online` with a permanent redirect, or
- Cloudflare DNS nameservers for the domain, then connect both the apex and `www`
  directly to Railway.

The Cloudflare approach is recommended if both hostnames must terminate directly
on Railway. Railway provisions and renews HTTPS certificates after DNS verification.

## Main routes

- `/` — landing page
- `/jobs/` — job search
- `/city-pools/` — city markets
- `/vault/` — technician workspace
- `/employer/` — employer workspace
- `/notifications/` — account updates
- `/billing/` — subscription and invoices
- `/account/login/` — sign in
- `/<DJANGO_ADMIN_URL>/` — private Django administration

## Security notes

- `.env` and uploaded media are ignored by Git.
- Production refuses to start without `DJANGO_SECRET_KEY`.
- Production refuses common/default admin paths.
- Account registration requires email verification.
- Job applications and saved-job changes require authenticated POST requests.
- Documents use randomized paths, a 10 MB file limit, a 100 MB vault quota,
  an hourly upload limit, a 12 MB request-body ceiling,
  extension/MIME/signature checks and forced downloads.
- Private files are available only to their technician, staff, or an employer with
  an active technician-approved credential request. Employer downloads also
  require the individual upload to be staff-verified; new files are quarantined.
- Application messages are limited to 600 characters and two unanswered messages.
- Job descriptions and profile fields have server-side length limits.
- Stripe webhooks require signature verification.
- Production cookies are secure and HTTP-only.
- Keep staging and production databases, Stripe keys and file storage isolated.
