# Vercel media storage (Supabase Storage)

Vercel's `/var/task` filesystem is read-only, so Django cannot persist uploaded result files or media there.
This project is already configured to use `django-storages` with any S3-compatible provider. On Vercel,
set `VERCEL=1` and provide the Supabase Storage S3 credentials below.

## 1. Create a Supabase Storage bucket

In Supabase Dashboard:

1. Open **Storage**.
2. Create a bucket, for example `curex-media`.
3. Keep it **private** because diagnostic results are patient data.

## 2. Enable S3 access and generate credentials

Open **Storage → Configuration → S3** (wording may vary slightly in the dashboard).
Enable the S3 protocol and generate an access key + secret key. Supabase only shows the secret once, so save it securely.

Supabase provides the S3 endpoint and project region on the S3 configuration page. For the endpoint, the direct storage hostname is recommended:

`https://<PROJECT_REF>.storage.supabase.co/storage/v1/s3`

The regular form is also supported:

`https://<PROJECT_REF>.supabase.co/storage/v1/s3`

## 3. Add these Vercel environment variables

Use **Vercel → Project → Settings → Environment Variables**. Add them for **Production** (and Preview if desired):

```text
VERCEL=1
USE_S3=True
AWS_ACCESS_KEY_ID=<Supabase S3 access key ID>
AWS_SECRET_ACCESS_KEY=<Supabase S3 secret key>
AWS_STORAGE_BUCKET_NAME=curex-media
AWS_S3_REGION_NAME=<Supabase project region, exactly as shown by Supabase>
AWS_S3_ENDPOINT_URL=https://<PROJECT_REF>.storage.supabase.co/storage/v1/s3
AWS_S3_ADDRESSING_STYLE=path
```

Do not put the real secret in GitHub, `.env.example`, or this file.

## 4. Redeploy

After saving the variables, redeploy the latest GitHub commit in Vercel.

The Django `FileField` storage backend automatically switches from local `media/` storage to Supabase S3 storage.
No database migration is required for this storage change.

## 5. Test

Log in as a lab user and upload a PDF/image at:

`/results/manage/upload/`

Then open the uploaded result. The file should be stored in Supabase Storage instead of `/var/task/media/...`.

### Important

Do not solve this by changing `MEDIA_ROOT` to `/tmp`. `/tmp` is ephemeral on serverless deployments and is not suitable for persistent patient results.

## Bundled diagnostic test images

The 87 realistic diagnostic test images are bundled under `static/img/tests/` and are served by
Django's static-file pipeline on Vercel. They are not dependent on the writable `/media/` filesystem
or on the Supabase bucket. This keeps the catalog images visible immediately after deployment.

The Supabase S3 bucket is still used for patient result uploads and any newly uploaded product media.
