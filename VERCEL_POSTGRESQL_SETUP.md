# Curex + Vercel + PostgreSQL Setup

The Vercel deployment must use PostgreSQL through DATABASE_URL. SQLite is only for local development.

## 1. Create a PostgreSQL database
Create a hosted PostgreSQL database (for example Neon, Supabase, or Vercel Postgres). Copy its full connection string.

## 2. Vercel environment variables
In Vercel: Project -> Settings -> Environment Variables, add for Production:

DATABASE_URL=<your full PostgreSQL connection string>
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<a new long random secret>
DJANGO_ALLOWED_HOSTS=curex-diagnostic-center.vercel.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://curex-diagnostic-center.vercel.app

The Curex Vercel host is also hard-coded in settings.py as a safe default.

## 3. Run migrations against PostgreSQL
Do NOT expect Vercel's request runtime to create tables. From your Windows project folder, temporarily set DATABASE_URL to the PostgreSQL connection string and run:

$env:DATABASE_URL="postgresql://..."
python manage.py migrate

This creates all tables in PostgreSQL.

## 4. Move existing SQLite data
With the existing SQLite database still configured, export data:

python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > curex-data.json

Then set DATABASE_URL to PostgreSQL and run migrations, followed by:

python manage.py loaddata curex-data.json

Do this carefully and keep a backup of db.sqlite3 first.

## 5. Push and redeploy
Once Vercel environment variables are set and PostgreSQL is migrated:

git add .
git commit -m "Configure PostgreSQL for Vercel deployment"
git push

## Important
Vercel's filesystem is not persistent for SQLite. Product/result uploads also need object storage (S3-compatible storage) for reliable production persistence.
