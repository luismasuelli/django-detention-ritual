__author__ = 'Luis'
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db.models.signals import post_syncdb
from django.dispatch import receiver
from django.conf import settings
import models


User = get_user_model()
create_user = settings.DJAILS_SPECIAL_USER_CREATE_FUNCTION


@receiver(post_syncdb, sender=models, dispatch_uid='group:ban', weak=False)
def setup_ban_users(**kwargs):
    """
    Setup the special users required for the ban feature.
    """

    if not issubclass(User, AbstractBaseUser):
        raise ImproperlyConfigured("Class %s (AUTH_USER_MODEL) does not specify a valid User class" % User.__name__)
    for s in models.SPECIAL_USERS:
        user, s = create_user(User, s)
        user.set_unusable_password()
        user.save()