from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate users using either their email address or username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_credential = username or kwargs.get('email') or kwargs.get('Username')
        if not login_credential or not password:
            return None

        login_credential = login_credential.strip()

        try:
            user = User.objects.get(
                Q(email__iexact=login_credential) | Q(username__iexact=login_credential)
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
