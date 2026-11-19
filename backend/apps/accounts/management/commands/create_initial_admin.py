import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Idempotently creates or updates the initial Django superuser for production "
        "using secure environment variables (DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD, "
        "and DJANGO_SUPERUSER_USERNAME). Safe to run on every deploy."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            dest='email',
            help='Superuser email address (overrides DJANGO_SUPERUSER_EMAIL env var)',
        )
        parser.add_argument(
            '--username',
            dest='username',
            help='Superuser username (overrides DJANGO_SUPERUSER_USERNAME env var)',
        )
        parser.add_argument(
            '--password',
            dest='password',
            help='Superuser password (overrides DJANGO_SUPERUSER_PASSWORD env var)',
        )
        parser.add_argument(
            '--update-password',
            action='store_true',
            dest='update_password',
            help='Update existing superuser password if already present',
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            dest='strict',
            help='Raise CommandError if credentials are not provided rather than skipping',
        )

    def handle(self, *args, **options):
        # 1. Resolve credentials from CLI options or Environment Variables
        email = (
            options.get('email')
            or os.getenv('DJANGO_SUPERUSER_EMAIL')
            or os.getenv('ADMIN_EMAIL')
        )
        username = (
            options.get('username')
            or os.getenv('DJANGO_SUPERUSER_USERNAME')
            or os.getenv('ADMIN_USERNAME')
        )
        password = (
            options.get('password')
            or os.getenv('DJANGO_SUPERUSER_PASSWORD')
            or os.getenv('ADMIN_PASSWORD')
        )
        update_password = (
            options.get('update_password')
            or os.getenv('DJANGO_SUPERUSER_UPDATE_PASSWORD', '').lower() in ('true', '1', 'yes')
        )
        strict = options.get('strict', False)

        # 2. Check required credentials
        if not email or not password:
            msg = (
                "Initial superuser creation skipped: DJANGO_SUPERUSER_EMAIL and/or "
                "DJANGO_SUPERUSER_PASSWORD environment variables are not set."
            )
            if strict:
                raise CommandError(msg)
            self.stdout.write(self.style.WARNING(f"[create_initial_admin] {msg}"))
            return

        email = email.strip()
        password = password.strip()
        if username:
            username = username.strip()
        else:
            username = email.split('@')[0]

        # 3. Idempotent user lookup & creation
        with transaction.atomic():
            user = User.objects.filter(email__iexact=email).first()
            if not user and username:
                user = User.objects.filter(username__iexact=username).first()

            if user:
                # User already exists
                updated = False
                if not user.is_superuser or not user.is_staff or getattr(user, 'role', '') != 'ADMIN':
                    user.is_superuser = True
                    user.is_staff = True
                    if hasattr(user, 'role'):
                        user.role = 'ADMIN'
                    updated = True

                if update_password:
                    user.set_password(password)
                    updated = True

                if updated:
                    user.save()
                    action_desc = "promoted to superuser and updated" if not user.is_superuser else "updated"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[create_initial_admin] Existing user '{user.email}' (username: {user.username}) was {action_desc}."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[create_initial_admin] Superuser '{user.email}' already exists. No changes needed."
                        )
                    )
            else:
                # Create brand new superuser using manager's create_superuser logic
                user = User.objects.create_superuser(
                    email=email,
                    username=username,
                    password=password,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[create_initial_admin] Superuser '{user.email}' (username: {user.username}) successfully created with role ADMIN."
                    )
                )
