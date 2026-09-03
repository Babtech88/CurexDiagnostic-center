from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_whatsapp_sales_workspace"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliveryrequest",
            name="payment_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="deliveryrequest",
            name="payment_reference",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
