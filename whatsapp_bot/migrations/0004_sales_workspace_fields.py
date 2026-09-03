from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("whatsapp_bot", "0003_whatsappcontact_assigned_agent"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsappcontact",
            name="conversation_status",
            field=models.CharField(
                choices=[("open", "Open"), ("pending", "Pending"), ("resolved", "Resolved")],
                default="open", max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="whatsappcontact",
            name="unread_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
