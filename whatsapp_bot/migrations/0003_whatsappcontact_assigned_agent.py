from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_staffprofile_public_bio_staffprofile_public_title_and_more"),
        ("whatsapp_bot", "0002_whatsappcontact_pending_date_text_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappcontact",
            name="assigned_agent",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_whatsapp_contacts", to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
