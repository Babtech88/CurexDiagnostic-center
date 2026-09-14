from django.conf import settings
from storages.backends.s3 import S3Storage


class SupabaseStorage(S3Storage):
    """
    Persistent storage for Curex uploaded files.

    Uses Supabase's S3-compatible Storage API.
    """

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    region_name = settings.AWS_S3_REGION_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL

    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY

    addressing_style = settings.AWS_S3_ADDRESSING_STYLE
    signature_version = settings.AWS_S3_SIGNATURE_VERSION

    default_acl = None

    # Prevent django-storages from performing HeadObject
    # before every upload.
    file_overwrite = True

    querystring_auth = True
    querystring_expire = 3600