import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a Django superuser from environment variables when it does not exist."

    def handle(self, *args, **options):
        username = self._get_env("DJANGO_SUPERUSER_USERNAME")
        email = self._get_env("DJANGO_SUPERUSER_EMAIL", required=False)
        password = self._get_env("DJANGO_SUPERUSER_PASSWORD")

        User = get_user_model()
        username_field = User.USERNAME_FIELD

        if User.objects.filter(**{username_field: username}).exists():
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists; skipping creation."))
            return

        create_kwargs = {
            username_field: username,
            "password": password,
        }
        if email and "email" in {field.name for field in User._meta.fields}:
            create_kwargs["email"] = email

        User.objects.create_superuser(**create_kwargs)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))

    def _get_env(self, name, required=True):
        value = os.environ.get(name)
        if required and not value:
            raise CommandError(f"{name} is required to create the initial superuser.")
        return value
