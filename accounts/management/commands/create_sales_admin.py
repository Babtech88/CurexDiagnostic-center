from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from accounts.models import StaffProfile

class Command(BaseCommand):
    help = "Create or update a dedicated Sales Admin account (separate from Django superuser admin)."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("password")
        parser.add_argument("--email", default="")

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=options["username"])
        user.email = options["email"] or user.email
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        user.set_password(options["password"])
        user.save()
        profile, _ = StaffProfile.objects.get_or_create(user=user)
        profile.role = StaffProfile.ROLE_SALES_MANAGER
        profile.is_active_staff = True
        profile.save()
        self.stdout.write(self.style.SUCCESS(
            f"Sales Admin '{user.username}' is ready. Login at /accounts/sales-admin/login/"
        ))
