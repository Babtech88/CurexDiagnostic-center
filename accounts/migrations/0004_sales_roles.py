from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_staffprofile_public_bio_staffprofile_public_title_and_more")]

    operations = [
        migrations.AlterField(
            model_name="staffprofile",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Administrator"),
                    ("manager", "Lab Manager"),
                    ("cashier", "Front Desk / Receptionist"),
                    ("sales_manager", "Sales Manager"),
                    ("sales_agent", "Sales Agent"),
                    ("lab_tech", "Lab Technician / Phlebotomist"),
                    ("delivery", "Sample Collection Rider"),
                ],
                default="cashier",
                max_length=20,
            ),
        ),
    ]
