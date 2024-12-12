from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings


class Command(BaseCommand):
    help = 'Create an admin user'

    def handle(self, *args, **options):
        user_model = get_user_model()
        if not user_model.objects.filter(is_superuser=True).exists():
            admin_email = settings.ADMIN_EMAIL
            admin_password = settings.ADMIN_PASSWORD
            user_model.objects.create_superuser(
                email=admin_email,
                password=admin_password
            )
            self.stdout.write(self.style.SUCCESS("Initial Superuser created successfully."))
        else:
            self.stdout.write(self.style.WARNING("A superuser already exists."))
