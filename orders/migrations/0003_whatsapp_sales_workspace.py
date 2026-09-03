from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_initial"),
        ("whatsapp_bot", "0004_sales_workspace_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="whatsapporder",
            name="contact",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="whatsapp_bot.whatsappcontact"),
        ),
        migrations.AddField(
            model_name="whatsapporder",
            name="payment_status",
            field=models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")], default="pending", max_length=20),
        ),
        migrations.AddField(
            model_name="whatsapporder",
            name="payment_reference",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
