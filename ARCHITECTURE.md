# WrenchLink Architecture and Engineering Handoff

This document is the primary technical handoff for developers and AI coding
agents continuing work on WrenchLink. Read it together with `README.md`,
`.env.example`, and the current migrations before changing the application.

## 1. Product summary

WrenchLink is a server-rendered automotive talent marketplace. It connects:

- automotive technicians who maintain a reusable professional profile ("Vault");
- employers such as repair shops, collision centers, dealerships, and fleets;
- platform staff who review documents, moderate accounts, and oversee activity.

The application is a Django monorepo. There is no separate React frontend or API
service. Django owns routing, authentication, HTML rendering, forms, validation,
database access, file authorization, email, billing synchronization, and staff
operations.

The production domain is intended to be:

```text
https://wrenchlink.online
https://www.wrenchlink.online
```

## 2. Current implementation status

Implemented:

- public landing page, job search, job detail, employer profiles, and City Pools;
- technician and employer registration with email verification;
- password reset through Django and SMTP;
- role-based dashboards;
- technician Vault/profile editing;
- education, work history, references, certifications, and private documents;
- employer profile editing, job CRUD, listing status controls, and talent search;
- application pipeline, invitations, interviews, offers, hiring, and withdrawal;
- application-specific messaging and anti-spam limits;
- credential access requests and permission-checked downloads;
- technician/employer reviews after a completed hire;
- configurable in-app and email notifications;
- branded staff operations panel;
- hidden Django administration with two-way navigation to the staff panel;
- moderation audit records and moderation notices;
- Stripe Checkout, Customer Portal, subscription synchronization, and invoices;
- PostgreSQL support, SQLite local fallback, Railway deployment configuration;
- private Railway-volume storage or optional S3-compatible storage;
- automated Django tests.

Not implemented:

- Twilio or SMS messaging;
- A2P consent collection, SMS opt-out handling, or SMS delivery logs;
- asynchronous task processing (Celery, RQ, Redis, etc.);
- real-time WebSockets/chat;
- a public JSON/REST/GraphQL API;
- React or another SPA frontend;
- automated antivirus or malware scanning;
- AWS deployment configuration beyond optional S3-compatible storage variables;
- advanced analytics, recommendation ML, or search indexing;
- organization/multi-user employer accounts;
- automated database backups inside application code.

Do not describe an unimplemented capability as live merely because related UI
copy exists.

## 3. Technology stack

| Layer | Technology |
|---|---|
| Application | Django 5.2 |
| Language | Python |
| Rendering | Django templates, HTML, CSS, small inline JavaScript |
| Production database | PostgreSQL |
| Local database | SQLite when PostgreSQL variables are absent |
| Static files | WhiteNoise + compressed manifest storage |
| Private uploads | Railway volume/filesystem or S3-compatible private bucket |
| Process server | Gunicorn, 3 synchronous workers |
| Email | SMTP, currently configured for Gmail-compatible settings |
| Payments | Stripe Checkout, Customer Portal, signed webhooks |
| Hosting | Railway |
| Tests | Django `TestCase` suite |

Dependencies are declared in `requirements.txt`.

## 4. Repository layout

```text
Wrenchlink/
├── accounts/                 # users, auth, registration, staff operations
│   ├── models.py             # User and ModerationAction
│   ├── forms.py              # login and registration forms
│   ├── views.py              # auth, verification, operations panel actions
│   ├── admin.py              # Django admin configuration
│   ├── urls.py
│   ├── tests.py
│   └── migrations/
├── marketplace/              # marketplace domain and most product behavior
│   ├── models.py             # profiles, jobs, applications, files, reviews
│   ├── forms.py
│   ├── views.py
│   ├── validators.py         # upload validation and quotas
│   ├── middleware.py         # request-body size limit
│   ├── context_processors.py # unread notification count
│   ├── management/commands/
│   │   └── seed_demo_data.py
│   ├── tests.py
│   └── migrations/
├── billing/                  # Stripe and local billing records
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── templates/
│   ├── base.html
│   ├── accounts/
│   ├── marketplace/
│   ├── billing/
│   ├── admin/base_site.html
│   └── errors/
├── assets/
│   ├── css/styles.css
│   ├── img/
│   └── js/
├── railway.toml
├── Procfile
├── requirements.txt
├── .env.example
├── README.md
└── manage.py
```

The root-level legacy files such as `index.html`, `jobs.html`, `employer.html`,
and `city-pools.html` are remnants/reference material from the pre-Django
frontend. The live application uses templates under `templates/`. Clean Django
routes permanently redirect the old `.html` URLs.

`staticfiles/` is generated by `collectstatic` and ignored by Git. Do not edit it
directly. Edit `assets/` instead.

## 5. Application boundaries

### `accounts`

Responsibilities:

- custom Django user model;
- technician/employer registration;
- email verification;
- login routing based on role;
- branded staff operations panel;
- moderation actions and audit history;
- direct staff notices by in-app notification and email.

The user roles are:

```text
technician
employer
admin
```

Authorization should not rely only on `role`. Platform control access is
protected with `is_staff`. Superusers are also staff.

### `marketplace`

Responsibilities:

- City Pools;
- technician and employer profiles;
- certifications, documents, employment history, education, references;
- jobs and saved jobs;
- applications and pipeline stages;
- application messages;
- credential-access requests;
- reviews;
- notifications and preferences;
- file upload validation and protected file serving.

Most marketplace behavior currently lives in `marketplace/views.py`. If this
file becomes difficult to maintain, split it by domain (for example,
`views/jobs.py`, `views/applications.py`, `views/vault.py`) without changing URL
names or authorization behavior.

### `billing`

Responsibilities:

- Stripe Checkout session creation;
- Stripe Customer Portal session creation;
- signed Stripe webhook processing;
- local subscription/invoice projections.

Stripe is the billing source of truth. The branded operations panel intentionally
shows billing data as read-only. Do not add local controls that modify
subscription state without making the equivalent Stripe API call and handling
webhook reconciliation.

## 6. Data model

### Accounts

#### `User`

Extends Django `AbstractUser`.

Important fields:

- `email`: unique but nullable for superusers;
- `role`: technician, employer, or administrator;
- `email_verified`;
- inherited `is_active`, `is_staff`, and `is_superuser`.

Registration uses email as the username. `createsuperuser` intentionally needs
only username and password.

#### `ModerationAction`

Immutable application-level audit record containing:

- staff actor;
- affected user;
- action identifier;
- subject/message;
- optional object type and object ID;
- creation timestamp.

The Django admin exposes these records as read-only.

### Profiles and geography

#### `CityPool`

A managed metro market with state, state code, region, slug, and active status.
It exposes database-backed technician and open-job counts.

The location dropdown includes `Other / location not listed`. This maps to a
null City Pool; it does not create a fake CityPool row.

#### `TechnicianProfile`

One-to-one with `User`. Contains:

- City Pool;
- title, bio, phone, years of experience;
- availability and schedule preferences;
- minimum pay and relocation preference;
- skills JSON list;
- visibility and notification-related flags.

#### `EmployerProfile`

One-to-one with `User`. Contains:

- company/shop identity;
- City Pool;
- description, contact information, website, address;
- perks JSON list;
- verification state: pending, verified, or rejected;
- legacy/compatibility `is_verified` boolean;
- rejection reason.

Keep `verification_status` and `is_verified` synchronized until a future
migration deliberately removes the boolean.

### Technician Vault records

- `Certification`: optional private file; pending/verified/rejected state.
- `TechnicianDocument`: private uploaded file; pending/verified/rejected state.
- `WorkHistory`.
- `Education`.
- `ProfessionalReference`.

Uploaded filenames are randomized by `private_upload_path()` and stored under:

```text
private/technicians/<technician-id>/<uuid>.<extension>
```

### Marketplace

#### `Job`

Belongs to an employer and City Pool. Supports:

- categories: repair, body, paint, estimator/advisor, EV/hybrid, diesel/fleet;
- schedules: full-time, part-time, contract;
- status: draft, active, paused, filled, closed;
- compensation range;
- experience/certification requirements;
- description and benefits;
- unique generated slug.

#### `Application`

Unique per technician/job pair. Pipeline stages:

```text
applied
invited
reviewed
interview
offered
hired
rejected
withdrawn
```

Stores employer notes, invitation message, offer details, and interview time.

#### Related models

- `SavedJob`;
- `ApplicationMessage`;
- `CredentialAccessRequest`;
- `TechnicianReview`;
- `EmployerReview`;
- `Notification`;
- `NotificationPreference`.

### Billing

#### `Subscription`

One-to-one with user. Stores Stripe IDs, plan, status, current period end, and
cancellation-at-period-end state.

#### `Invoice`

Stores the Stripe invoice ID, amount, currency, status, hosted invoice URL, PDF
URL, and creation timestamp.

## 7. Primary workflows

### Registration and authentication

1. User chooses technician or employer registration.
2. The form creates `User` plus the matching profile in one transaction.
3. The user receives a tokenized email-verification link.
4. Unverified non-staff users cannot log in.
5. `/account/dashboard/` routes:
   - staff to `/account/operations/`;
   - employers to `/employer/`;
   - technicians to `/vault/`.

### Technician Vault

Technicians can:

- edit profile and visibility;
- select a City Pool or “Other / location not listed”;
- upload private documents and certifications;
- add/remove work history, education, and references;
- review applications and saved jobs;
- respond to invitations and offers;
- manage notification settings.

Vault POST operations use an `action` field to select the form/action. Preserve
this convention unless refactoring the endpoint and templates together.

### Employer workflow

Employers can:

- edit a business profile;
- create, edit, pause, activate, fill, close, or delete jobs;
- search visible technicians;
- invite technicians to a specific job;
- request access to private credentials;
- manage applications on a tabbed pipeline board;
- schedule interviews, send offers, and mark hires;
- message applicants;
- review hired technicians.

### Application messaging

Messages are application-scoped and visible only to the participating technician,
the employer that owns the job, or staff.

Message bodies are limited to 600 characters. A spam guard prevents a party from
sending a third consecutive unanswered message.

### Credential access and private documents

An employer cannot access a technician’s private files merely by viewing the
profile.

Access requires:

1. an approved `CredentialAccessRequest`;
2. the individual document/certification to be staff verified;
3. the requesting employer to match the approved request.

Owners and staff retain access. Files are returned through Django `FileResponse`
as attachments with no-store and `nosniff` headers. `MEDIA_ROOT` is not publicly
served.

### Staff operations

The branded panel is:

```text
/account/operations/
```

It requires `is_staff` and supports:

- account activation/suspension;
- manual email verification;
- direct staff messages;
- document/certification approval or rejection;
- required reasons for adverse actions;
- employer verification/rejection;
- technician profile visibility moderation;
- job status moderation;
- billing visibility;
- moderation audit history.

Moderation notices are written directly to `Notification`, emailed when the user
has an email address, and recorded as `ModerationAction`.

The private Django admin remains available at `/<DJANGO_ADMIN_URL>/`. Each admin
surface links to the other.

### Notifications

Marketplace notifications can use:

- in-app delivery;
- synchronous SMTP email.

User preferences cover messages, applications, offers, credential requests, and
matching jobs. Staff/system moderation notices bypass these optional preferences
and are created directly because account/safety notices must be delivered.

There is no background queue. SMTP calls happen during the web request.

### Billing

1. A logged-in user selects a permitted plan.
2. Django creates/reuses a local `Subscription` and Stripe customer.
3. Stripe Checkout handles payment.
4. Stripe webhooks synchronize subscriptions and invoices.
5. The Customer Portal handles customer-managed billing changes.

Allowed plan mapping:

- technician: `solo`;
- employer: `starter` or `pro`.

The Enterprise card is currently a contact-sales path, not a Stripe checkout
plan.

## 8. URL map

Important public/application routes:

```text
/                                      landing page
/jobs/                                 job search
/jobs/<slug>/                          job detail
/city-pools/                           City Pool directory
/technicians/<id>/                     technician profile
/employers/<id>/                       employer profile
/vault/                                technician dashboard
/employer/                             employer dashboard
/applications/<id>/                   application workspace
/notifications/                        notification center
/billing/                              billing overview
/legal/                                legal content
/health/                               health endpoint
```

Account routes:

```text
/account/login/
/account/logout/
/account/register/technician/
/account/register/employer/
/account/dashboard/
/account/operations/
/account/password-reset/
```

Administrative route:

```text
/<DJANGO_ADMIN_URL>/
```

Use Django URL names (`reverse()` or `{% url %}`), not hard-coded paths, when
adding application links.

## 9. Templates and styling

The site is server-rendered.

- Base layout: `templates/base.html`
- Main stylesheet: `assets/css/styles.css`
- Landing page: `templates/marketplace/home.html`
- Branded staff panel: `templates/accounts/operations.html`
- Django admin override: `templates/admin/base_site.html`

Design constraints established during development:

- retain WrenchLink navy/orange/cream brand colors;
- avoid browser-default/select styling;
- avoid underlined button-like links;
- dashboards use tabs rather than one long page;
- desktop pricing shows four cards, tablet two, mobile one;
- hero artwork remains on the right and must not overlap copy;
- mobile layouts must remain readable and avoid horizontal page overflow.

The hero asset is:

```text
assets/img/wrenchlink-hero-platform.png
```

It is an RGBA transparent illustration. Do not replace it with an opaque white
JPG or position it over the headline.

## 10. Configuration

All secrets and environment-specific values belong in environment variables.
Never commit `.env`.

Core Django variables:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ADMIN_URL
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
DJANGO_TIME_ZONE
DJANGO_SECURE_SSL_REDIRECT
```

Database variables:

```text
USE_POSTGRES
DB_NAME / PGDATABASE
DB_USER / PGUSER
DB_PASSWORD / PGPASSWORD
DB_HOST / PGHOST
DB_PORT / PGPORT
DB_SSLMODE
```

Email variables:

```text
EMAIL_BACKEND
EMAIL_HOST
EMAIL_PORT
EMAIL_USE_TLS
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL
```

Storage variables:

```text
RAILWAY_VOLUME_MOUNT_PATH
MEDIA_ROOT
AWS_STORAGE_BUCKET_NAME
AWS_S3_ENDPOINT_URL
AWS_S3_REGION_NAME
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

Stripe variables:

```text
STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_TECH_PRICE_ID
STRIPE_STARTER_PRICE_ID
STRIPE_PRO_PRICE_ID
```

See `.env.example` for the canonical list.

## 11. Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Optional demo data:

```bash
python manage.py seed_demo_data
```

The seed command:

- is intended for local/staging environments;
- is idempotent;
- refuses normal production use when debug is disabled;
- does not replace existing superusers;
- is application code, not a committed database.

Never commit `db.sqlite3`, PostgreSQL dumps, user uploads, `.env`, or generated
`staticfiles/`.

## 12. Railway deployment

The repository uses `railway.toml`:

```text
build:      SKIP_DATABASE_CONFIG=True python manage.py collectstatic --noinput
pre-deploy: python manage.py migrate --noinput
start:      gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
```

The pre-deploy migration container stopping is expected. Railway then starts a
separate application container. Gunicorn logs startup information to stderr, so
Railway may label normal `[INFO]` lines as `[err]`.

Recommended services per environment:

```text
Web service (public)
PostgreSQL service (private)
Volume mounted to Web at /data
```

Use separate staging and production environments with:

- different PostgreSQL databases;
- different Django secret keys;
- different private admin paths;
- separate media volumes;
- Stripe test keys in staging and live keys in production;
- environment-appropriate domains and mail settings.

The production and staging sites should not share databases or media volumes.

## 13. Storage behavior

### Railway volume

When `RAILWAY_VOLUME_MOUNT_PATH=/data`, default media storage becomes:

```text
/data/media
```

The PostgreSQL volume stores database files only. It does not persist uploaded
documents. The web service needs its own media volume.

### S3-compatible storage

When `AWS_STORAGE_BUCKET_NAME` is present, Django uses private
`storages.backends.s3.S3Storage` with signed URLs and no overwrite.

Permission checks must still happen before returning or redirecting to a private
object. Do not make the bucket public.

## 14. Security controls

Current controls include:

- production secret-key requirement;
- production rejection of common/default admin paths;
- HTTPS redirect and proxy SSL handling;
- HSTS, secure cookies, HTTP-only cookies, referrer policy, and frame denial;
- CSRF protection;
- email verification;
- role/ownership checks in views;
- POST-only state changes;
- Stripe webhook signature verification;
- 12 MB request-body middleware limit;
- 10 MB per uploaded file;
- 100 MB per-technician private-vault quota;
- 20 uploads per hour;
- extension, MIME, and magic-byte/signature validation;
- randomized private file paths;
- private permission-checked file responses;
- staff verification before employer document access;
- moderation audit history;
- server-side text-length constraints;
- application message spam guard.

Known limitations:

- file validation is not antivirus scanning;
- email is synchronous and can slow requests;
- throttling is application-level and not a general rate-limiting system;
- no two-factor authentication is implemented;
- staff authorization is binary (`is_staff`), without granular staff roles;
- moderation object references are generic IDs rather than database foreign keys.

## 15. Testing and required verification

Run before committing:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
git diff --check
```

At the time of this handoff, the full suite contains 40 tests covering:

- authentication and email verification;
- role routing;
- operations-panel authorization;
- moderation actions, reasons, email, in-app notices, and audit records;
- location dropdown fallback;
- job ownership and status changes;
- dashboard tabs and pipeline behavior;
- invitation, offer, acceptance, and reviews;
- notification preferences;
- message spam limits;
- private document validation and permissions;
- demo-data idempotency;
- Stripe webhook signature rejection;
- HTTPS health behavior.

When fixing a bug, add a regression test near the relevant existing tests.

## 16. Safe extension guidelines for AI agents

Before modifying behavior:

1. Inspect the current model, migration history, form, view, template, and tests.
2. Preserve unrelated local changes; the repository may have a dirty worktree.
3. Use Django migrations for every schema change.
4. Keep authorization on the server. Hiding a button is not access control.
5. Use POST for state changes and retain CSRF tokens.
6. Preserve route names where possible.
7. Never expose `MEDIA_ROOT` through a public static-media route.
8. Keep Stripe state provider-driven.
9. Do not seed production automatically.
10. Update this document when adding a major subsystem.

For a new integration, document:

- environment variables;
- database models;
- permissions;
- webhook/authentication rules;
- retry/idempotency behavior;
- tests;
- deployment changes.

## 17. Recommended next engineering work

Prioritized candidates:

1. Split the large marketplace and operations view modules by domain.
2. Add pagination to staff tables, job search, notifications, and talent search.
3. Add granular staff permissions (support, trust/safety, billing).
4. Move email delivery to a background queue before higher-volume production.
5. Add antivirus scanning/quarantine workflow for uploads.
6. Add structured audit metadata and IP/request identifiers.
7. Add database and media backup/restore runbooks.
8. Improve observability with structured logging and error tracking.
9. Add browser-level responsive/accessibility tests.
10. Add SMS only after implementing consent records, STOP/HELP handling,
    provider compliance, delivery status, and secure phone normalization.

## 18. Twilio/SMS note

Twilio is not installed and SMS is not currently sent by WrenchLink.

If one-to-one requested SMS is added later, it still requires a deliberate
compliance design for US application-originated messaging. Do not merely add a
Twilio API call. At minimum add:

- explicit consent capture and timestamp/source records;
- phone normalization and validation;
- consent text linked to privacy policy and terms;
- STOP/HELP processing and suppression records;
- message-purpose restrictions;
- delivery status callbacks and logs;
- provider credentials in environment variables;
- tests preventing sends without consent;
- the appropriate Twilio sender registration/verification.

Email and in-app notifications remain the currently supported channels.

