# Curex Diagnostic Center — Management Platform

A full Django web app for **Curex Diagnostic Center** (Adeleke University Road, Isale Ilori,
Close to Olabebo, Ede, Osun State) covering:

- Public patient-facing storefront advertising active sales/promotions, with your logo,
  motto ("ACCURATE RESULT, COMPASSIONATE CARE."), address, phone, and email in the header/footer
- Full service catalog (Haematology, Clinical Chemistry, Blood Serology, Microbiology &
  Parasitology, Semen Analysis, Skin Tests, Ultrasound Scan, Pregnancy Test, Hormonal
  Profiles, ECG) plus reagents/kits & consumables
- Reagent/kit **expiry date tracking** with a 30-day warning window
- **Low-stock alerts** for reagents and consumables
- **Sales/booking reporting** with revenue, profit, and top-test charts (Chart.js)
- **Staff management** with separate logins and role-based permissions (Administrator, Lab Manager, Sales Manager, Sales Agent, Front Desk, Lab Technician, Sample Collection Rider)
- **Patient records** with booking/order history
- **WhatsApp booking**: patients build a cart on the public site, submit their details, and
  are redirected to a pre-filled `wa.me` link to confirm with your front desk
- **Home sample collection requests**, with rider assignment and status tracking
- Promotions/advertised sales tied to specific tests

## 1. Requirements

- Python 3.11+ (project was built and tested on Python 3.12 / Django 6.0)
- pip

## 2. Setup

```bash
cd curex-diagnostic-center
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo_data   # optional: creates demo staff, full service catalog, patients
python manage.py runserver
```

Visit:
- **Public site:** http://127.0.0.1:8000/
- **Staff login:** http://127.0.0.1:8000/accounts/login/
- **Django admin:** http://127.0.0.1:8000/admin/

### Demo accounts (created by `seed_demo_data`)

| Username   | Password       | Role                          |
|------------|----------------|--------------------------------|
| admin      | admin12345     | Administrator (superuser)     |
| labtech    | labtech12345   | Lab Technician / Phlebotomist |
| frontdesk  | frontdesk12345 | Front Desk / Receptionist     |

**Change these passwords before deploying to production.**

## 3. Key settings to review before going live

Open `salesplatform/settings.py`:

- `SITE_NAME`, `SITE_MOTTO`, `SITE_ADDRESS`, `SITE_PHONE`, `SITE_EMAIL` — business identity,
  shown site-wide via a context processor.
- `WHATSAPP_BUSINESS_NUMBER` — international format, digits only (currently set to
  `2349122997406` for 09122997406). This is the number patients' booking messages are sent to.
- `EXPIRY_WARNING_DAYS` — how many days ahead of expiry a reagent/kit is flagged (default 30).
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` — **must** be changed for production. Generate a new
  `SECRET_KEY`, set `DEBUG = False`, and list your real domain(s) in `ALLOWED_HOSTS`.
- `EMAIL_BACKEND` — currently prints emails to the console. Point this at a real SMTP backend
  (e.g. Gmail, SendGrid) to receive the daily alert emails for real.

## 4. Logo

The uploaded logo lives at `static/img/logo.jpeg` and is referenced throughout the templates
(navbar, footer, login page, sidebar, homepage hero). Swap that file for a higher-resolution
version any time — no code changes needed as long as the filename stays `logo.jpeg`, or update
the `{% static 'img/logo.jpeg' %}` references if you rename it.

## 5. Daily alerts (low stock & expiring reagents)

Run this manually, or wire it into cron / a scheduled task to email admins automatically:

```bash
python manage.py check_alerts
```

Example cron entry (runs every morning at 7am):
```
0 7 * * * cd /path/to/project && venv/bin/python manage.py check_alerts
```

## 6. Project structure

```
salesplatform/     # Django project settings, root urls, context processor
accounts/          # Staff profiles, roles, login/logout, staff CRUD
inventory/         # Tests/services/reagents, categories, suppliers, promotions, alerts
sales/             # Booking (POS-style) entry, booking history, reporting
customers/         # Patient records
orders/            # Public WhatsApp cart/checkout + staff booking & sample-collection management
dashboard/         # Staff homepage with KPIs, alerts, recent activity
templates/          # All HTML templates (base.html = staff layout, base_public.html = patient site)
static/img/logo.jpeg  # Your uploaded logo
```

## 7. Adding/editing tests, prices, and reagents

Log in as `admin`, go to **Tests & Services** in the sidebar (`/inventory/`) to add, edit,
restock, or retire any test, scan, or reagent. Use **Promotions** (`/inventory/promotions/`)
to advertise a discount on any set of tests — it will automatically show on the public
homepage while active.

### Updating the official price list

The catalog is loaded from `inventory/management/commands/load_official_price_list.py`, which
contains the exact 78-test Curex price list (Clinical Chemistry, Haematology & Blood Group
Serology, Microbiology, Scan, ECG). If prices change:

```bash
python manage.py load_official_price_list
```

This is safe to re-run any time — it matches tests by name and updates the price rather than
duplicating entries, and deactivates (never deletes) any old test that's no longer on the list.
To edit the actual prices, open that file and change the numbers directly, or just edit
individual tests in the dashboard at `/inventory/`.

Every test also has a category-based illustration (generated originals, not stock photos —
see `static/img/categories/`). To (re)assign images to any test missing one:

```bash
python manage.py assign_test_images
```

## 9. WhatsApp Auto-Reply Bot

The app includes a smart auto-reply bot on your business number (**+2349122997406**) built on
Meta's official **WhatsApp Cloud API** — no unofficial/ban-risk libraries involved.

**What it does out of the box:**
- 🏥 Menu-driven access to book appointments, check prices, check availability, get location
  & hours, or reach a human
- 📅 **Multi-step appointment booking** — patient picks a test, gives a preferred date/time,
  confirms, and a booking request lands in the staff dashboard automatically
- 💰 **Live prices** pulled straight from your test catalog (typing "malaria" or "FBC" returns
  the real price from the database — never a stale hardcoded number)
- 🧪 **Availability checks** — reports whether a test/reagent is in stock, low, or unavailable
- 🤖 **AI-powered replies** (optional) for open-ended questions the menu doesn't cover — "do I
  need to fast before an FBS test?" gets a real, grounded answer via Claude, with guardrails so
  it never invents prices or gives medical diagnoses
- 👨‍⚕️ **Escalates to a human** on request — the bot goes quiet on that chat until staff reply
  or the patient types MENU again
- 📧 **Notifies staff by email** the moment a new appointment comes in or a patient asks for a
  human — configurable recipient list, safe to leave unset (just skips silently)
- 🗂️ **Every message saved** to the database — full conversation history per patient, visible
  in the staff dashboard

**Staff-facing pages added:**
- `/whatsapp-bot/conversations/` — read any chat, reply manually (clears the "needs human" flag)
- `/whatsapp-bot/appointments/` — confirm/cancel bot-originated bookings; confirming one
  automatically messages the patient on WhatsApp
- Two new KPI cards on the main dashboard: pending appointments, chats needing a human

### 9.1 Get your Meta credentials (if you haven't already)

1. Go to https://developers.facebook.com/, create a **Meta Business App** (type: Business),
   and add the **WhatsApp** product to it.
2. Under WhatsApp → API Setup, either use the test number Meta gives you first, or add/verify
   your real number (+2349122997406) as the business phone number. Note the **Phone Number ID**.
3. Generate a **permanent access token**: System Users → create a system user → assign it to
   your WhatsApp app with `whatsapp_business_messaging` permission → generate token (choose
   "Never expire" if offered, otherwise you'll need to refresh it periodically).
4. Fill in `.env` (copy from `.env.example` if you don't have one yet):
   ```
   WHATSAPP_CLOUD_API_TOKEN=<your permanent token>
   WHATSAPP_PHONE_NUMBER_ID=<phone number ID from step 2>
   WHATSAPP_VERIFY_TOKEN=curex-verify-2026
   ```
   `.env` is gitignored — never commit it or paste its contents anywhere public. If a token
   ever leaks, revoke it immediately (System Users → your token → Revoke) and generate a new one.
5. Verify it's working:
   ```bash
   python manage.py check_whatsapp_connection
   ```
   This calls Meta's Graph API directly and reports your verified business name, phone number,
   and WhatsApp quality rating if everything's working, or the exact error if not.

### 9.2 Fastest way to test with a real WhatsApp message today (ngrok)

You don't need to deploy anywhere to try this out — a tunnel to your own laptop is enough for
testing (not for running the business long-term, since it dies when your laptop sleeps/closes):

1. Install ngrok: https://ngrok.com/download (free account is enough), then `ngrok config add-authtoken <your token>`.
2. In one terminal: `python manage.py runserver`
3. In another terminal: `ngrok http 8000`
4. ngrok prints a public URL like `https://a1b2-c3d4.ngrok-free.app` — copy it.
5. In the Meta dashboard, under WhatsApp → Configuration → Webhook, set:
   - **Callback URL:** `https://a1b2-c3d4.ngrok-free.app/whatsapp-bot/webhook/`
   - **Verify Token:** `curex-verify-2026` (or whatever you set `WHATSAPP_VERIFY_TOKEN` to)
   - Click **Verify and Save** — Meta will hit your ngrok URL immediately; if `runserver` is
     running you should see a `GET /whatsapp-bot/webhook/` 200 in its logs
   - Subscribe to the **messages** webhook field
6. Send a WhatsApp message to +2349122997406 from your phone. You should get the menu reply
   within a few seconds, and see it appear at `/whatsapp-bot/conversations/`.

Note: `SITE_BASE_URL` in `.env` won't be your ngrok URL — leave it as your eventual real domain;
it's only used to build links the bot sends in messages (e.g. "browse our catalog at...").

### 9.3 Real deployment (so it runs without your laptop)

The project is ready for a standard Python host — it ships with `gunicorn`, `whitenoise` for
static files, and a `Procfile`. Any platform that reads a `Procfile` (Railway, Render, Heroku-
style hosts) works with roughly these steps:

1. Push the project to a Git repo (the included `.gitignore` already keeps `.env`, `venv/`,
   and `db.sqlite3` out of it).
2. Create a new app on your platform of choice, pointed at that repo.
3. Set these as environment variables in the platform's dashboard (not in a committed file):
   ```
   DJANGO_SECRET_KEY=<the one already in your local .env — copy it over, or generate a new one>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=<your platform's assigned domain, e.g. curex.up.railway.app>
   DJANGO_CSRF_TRUSTED_ORIGINS=https://<same domain>
   SITE_BASE_URL=https://<same domain>
   WHATSAPP_CLOUD_API_TOKEN=<your token>
   WHATSAPP_PHONE_NUMBER_ID=<your phone number id>
   WHATSAPP_VERIFY_TOKEN=curex-verify-2026
   ANTHROPIC_API_KEY=<optional>
   STAFF_NOTIFICATION_EMAILS=<optional>
   ```
4. Most platforms auto-detect the `Procfile` and run `gunicorn salesplatform.wsgi:application`
   for you, plus `python manage.py migrate` on release. If yours doesn't, run those manually.
5. Once deployed, repeat step 5 from section 9.2 above but with your real domain instead of the
   ngrok URL — that's the one-time switch from "testing" to "live in production."
6. For real email delivery of staff notifications, also set a real `EMAIL_BACKEND` in
   `settings.py` (it currently prints emails to the server console) — e.g. Gmail SMTP,
   SendGrid, or Postmark, following Django's standard `EMAIL_*` settings.

### 9.4 Sales team workspace and separate logins

The staff system now supports dedicated sales accounts. Administrators can create any staff role; Sales Managers can create Sales Agent accounts. Each user signs in at `/accounts/login/` with their own username and password.

- `/accounts/staff/` — staff account management
- `/accounts/sales-team/` — sales team performance and WhatsApp workload
- Sales Agents see their own recorded sales and only WhatsApp conversations assigned to them.
- Sales Managers and Administrators can view team workloads and assign WhatsApp conversations.
- Administrators can reset a staff member's password from the staff edit form; leave the field blank to keep the existing password.

### 9.5 Customizing the bot's replies, menu, and AI guardrails

Edit `whatsapp_bot/bot_engine.py` — the menu text, appointment flow, and matching logic all live
there in plain Python. The price/availability lookups automatically exclude your "Reagents &
Kits" and "Consumables" categories so patients only ever see billable tests, scans, and packages.

The AI fallback's behavior and boundaries (what it will and won't answer) are defined in the
`SYSTEM_PROMPT_TEMPLATE` at the top of `whatsapp_bot/ai_reply.py` — edit that prompt to adjust
tone or add more specific guidance (e.g. your actual fasting/prep instructions per test type).

### 9.5 Local testing without any live credentials

You can exercise the full bot logic — including the appointment flow — without any WhatsApp or
Anthropic credentials:

```bash
python manage.py shell -c "
from whatsapp_bot.models import WhatsAppContact
from whatsapp_bot.bot_engine import handle_incoming_message
c = WhatsAppContact.objects.create(wa_id='2348000000000', profile_name='Test')
print(handle_incoming_message(c, 'hi'))
print(handle_incoming_message(c, '1'))
print(handle_incoming_message(c, 'malaria'))
print(handle_incoming_message(c, 'Friday morning'))
print(handle_incoming_message(c, 'yes'))
c.delete()
"
```

## 9.6 Test Results Upload & Patient Print Portal

Staff can upload a patient's result (PDF or image) against their record from **Staff Dashboard
→ Test Results → Upload Result**. Each upload gets a random 8-character access code (e.g.
`CFEUCE2T`) that, combined with the patient's phone number, is the only way to view it.

- **"Send Result Link to Patient"** on the result's detail page sends the phone number + code to
  the patient via WhatsApp automatically (reuses the same Cloud API connection as the bot).
- Patients go to `/results/` (linked in the site nav as "Patient Portal"), enter their phone
  number and code, and land on a print-friendly page — a "Print This Result" button, plus an
  "Open Full File in New Tab" link that uses the browser's native PDF viewer for a more reliable
  print/save-as-PDF experience for larger files.
- Phone number matching is lenient on purpose — `08030000099` and `2348030000099` are treated as
  the same number (matches on the last 10 digits), so it doesn't matter which format staff or
  patients type it in.
- Uncheck **"Released to Patient"** on a result to hide it from the portal without deleting it
  (e.g. if it needs review before release).
- **Deploying this to Render or similar?** See section 10.2 below — uploaded result files need
  S3-compatible storage in production, or they'll be lost on redeploy.

## 10. Deploying to Render.com

The project is ready for Render out of the box — it uses PostgreSQL in production (via
`DATABASE_URL`) instead of SQLite, because **Render's disk is wiped on every deploy and
restart**. If it stayed on SQLite, you'd lose every patient, booking, and test result the
moment you redeployed.

### 10.1 One-click-ish deploy with the included Blueprint

1. Push this project to a GitHub (or GitLab) repository. The included `.gitignore` already
   keeps `.env`, `venv/`, `db.sqlite3`, and `staticfiles/` out of it.
2. On https://dashboard.render.com/, click **New +** → **Blueprint**, and point it at your repo.
   Render will read `render.yaml` and set up:
   - A free PostgreSQL database (`curex-db`)
   - A free web service running `gunicorn`, with `collectstatic` and `migrate` run automatically
     on every deploy
   - `DJANGO_SECRET_KEY` auto-generated for you
3. Render will prompt you to fill in the env vars marked `sync: false` in `render.yaml` — these
   are the ones it can't safely generate for you:
   ```
   DJANGO_ALLOWED_HOSTS=<your-app-name>.onrender.com
   DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-app-name>.onrender.com
   SITE_BASE_URL=https://<your-app-name>.onrender.com
   WHATSAPP_CLOUD_API_TOKEN=<your token>
   WHATSAPP_PHONE_NUMBER_ID=<your phone number id>
   ANTHROPIC_API_KEY=<optional>
   STAFF_NOTIFICATION_EMAILS=<optional>
   ```
4. Deploy. Render builds and starts the app, running migrations against the new Postgres
   database automatically (see the `buildCommand` in `render.yaml`).
5. Visit `https://<your-app-name>.onrender.com/admin/` — there's no seeded data on a fresh
   Postgres database, so create your first admin account with Render's **Shell** tab:
   ```bash
   python manage.py createsuperuser
   ```
   Or, if you want the full demo catalog (all 81 Curex tests, categories, a promotion):
   ```bash
   python manage.py seed_demo_data
   ```
6. Update your WhatsApp webhook in the Meta dashboard to point at your new Render URL:
   `https://<your-app-name>.onrender.com/whatsapp-bot/webhook/` (see section 9.3).

### 10.2 Don't deploy without reading this: media storage

Render's free web service disk is **ephemeral** — anything written to it (uploaded test
results, product images, testimonial photos) disappears on the next deploy or restart. This
directly breaks the results feature you just asked for, so before you rely on this in
production:

- Set `USE_S3=True` in Render's environment variables, plus `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`, and `AWS_STORAGE_BUCKET_NAME` for an S3-compatible bucket. Any of
  these work fine and all have cheap/free tiers:
  - **Cloudflare R2** — no egress fees, generous free tier. Set `AWS_S3_ENDPOINT_URL` to your
    account's R2 endpoint.
  - **AWS S3** — the original; leave `AWS_S3_ENDPOINT_URL` blank, just set `AWS_S3_REGION_NAME`.
  - **Backblaze B2** or **DigitalOcean Spaces** — also S3-compatible, same env vars.
- Without this, everything else in the app (bookings, patients, prices, appointments) is safe
  in Postgres — it's specifically **uploaded files** that need it.
- Free-tier Render web services also spin down after inactivity and take ~30-60 seconds to
  wake up on the next request — expected behavior, not a bug, but worth knowing before a demo.

### 10.3 Alternative hosts

Nothing here is Render-specific except `render.yaml` itself — the same `Procfile` +
`requirements.txt` + `DATABASE_URL` pattern works on Railway, Fly.io, or any host that runs a
`Procfile`-style Python app with an attached Postgres database.

## 11. Notes on scope / what to extend next

- Payment gateway integration (e.g. Paystack/Flutterwave) is not wired in — bookings are
  currently marked paid manually by staff. Hook this into the checkout flow if you want online
  prepayment.
- **Testimonials, health articles, and the "Meet Our Specialists" backend are real, staff-managed
  content — not filled with placeholder data.** Testimonials and articles sections simply don't
  render on the homepage until you add real ones (Staff Dashboard → Testimonials / Health
  Articles). The homepage's "Equipment Behind Your Results" section replaced a Doctors/Specialists
  section per your request — the backend for opting real staff into a public bio (with photo,
  title, bio) still exists at Staff Dashboard → note: only reachable via
  `/content/staff-profiles/` currently, not yet linked from a homepage section — wire it back in
  if you want a "Meet the Team" section later.
- Homepage stats (tests offered, specialties covered) are computed live from your actual catalog
  — I deliberately didn't hardcode marketing numbers like "5000+ patients" or "99% accuracy"
  since I have no real figures to back them; swap in real ones in `storefront/home.html` if/when
  you have them verified.
- Staff notifications are email-only for now. WhatsApp-to-staff notifications are possible but
  need an approved Meta message template (Cloud API only allows free-form replies within a
  24-hour window of the *patient's* last message, not arbitrary outbound pings to staff numbers).
- The bot currently only handles text and simple button/list replies; images, voice notes, and
  location messages are logged but not deeply processed — extend `_process_single_message` in
  `whatsapp_bot/views.py` if you want to handle those (e.g. auto-transcribe voice notes).
- Meta access tokens from a System User can be set to not expire, but tokens tied to a personal
  account expire in ~60 days — use a System User token for anything you deploy long-term.



## Sales Admin
Create a separate non-superuser Sales Admin:
`python manage.py create_sales_admin USERNAME PASSWORD --email EMAIL`
Login: `/accounts/sales-admin/login/`

## Product images
`MEDIA_URL` is configured as `/media/` so product JPG paths resolve correctly from catalog and nested pages.
