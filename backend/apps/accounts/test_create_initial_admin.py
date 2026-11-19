import os
from io import StringIO
from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()


class CreateInitialAdminCommandTests(TestCase):
    def test_command_skips_cleanly_when_no_credentials(self):
        out = StringIO()
        call_command('create_initial_admin', stdout=out)
        output = out.getvalue()
        self.assertIn("Initial superuser creation skipped", output)

    def test_command_creates_superuser_via_arguments(self):
        out = StringIO()
        call_command(
            'create_initial_admin',
            email='bootstrap_admin@example.com',
            username='bootstrap_admin',
            password='SecurePassword123!',
            stdout=out
        )
        output = out.getvalue()
        self.assertIn("successfully created with role ADMIN", output)
        # Check user in DB
        admin_user = User.objects.get(email='bootstrap_admin@example.com')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertEqual(admin_user.role, 'ADMIN')
        self.assertTrue(admin_user.check_password('SecurePassword123!'))

    def test_command_is_idempotent(self):
        out1 = StringIO()
        call_command(
            'create_initial_admin',
            email='idempotent_admin@example.com',
            username='idempotent_admin',
            password='SecurePassword123!',
            stdout=out1
        )
        self.assertIn("successfully created", out1.getvalue())

        # Second call should not create duplicate and should report already exists
        out2 = StringIO()
        call_command(
            'create_initial_admin',
            email='idempotent_admin@example.com',
            username='idempotent_admin',
            password='SecurePassword123!',
            stdout=out2
        )
        self.assertIn("already exists", out2.getvalue())
        self.assertEqual(User.objects.filter(email='idempotent_admin@example.com').count(), 1)

    def test_command_creates_superuser_from_env_vars(self):
        env_dict = {
            'DJANGO_SUPERUSER_EMAIL': 'env_admin@example.com',
            'DJANGO_SUPERUSER_USERNAME': 'env_admin',
            'DJANGO_SUPERUSER_PASSWORD': 'EnvPassword123!',
        }
        with patch.dict(os.environ, env_dict):
            out = StringIO()
            call_command('create_initial_admin', stdout=out)
            output = out.getvalue()
            self.assertIn("successfully created with role ADMIN", output)

            user = User.objects.get(email='env_admin@example.com')
            self.assertTrue(user.is_superuser)
            self.assertTrue(user.is_staff)
            self.assertEqual(user.role, 'ADMIN')
            self.assertTrue(user.check_password('EnvPassword123!'))

    def test_command_updates_password_when_flag_passed(self):
        # Create first
        call_command(
            'create_initial_admin',
            email='change_pwd@example.com',
            username='change_pwd',
            password='OldPassword123!'
        )
        user = User.objects.get(email='change_pwd@example.com')
        self.assertTrue(user.check_password('OldPassword123!'))

        # Update password
        out = StringIO()
        call_command(
            'create_initial_admin',
            email='change_pwd@example.com',
            username='change_pwd',
            password='NewPassword456!',
            update_password=True,
            stdout=out
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword456!'))
        self.assertFalse(user.check_password('OldPassword123!'))
