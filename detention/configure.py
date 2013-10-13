from django.contrib.auth import get_user_model
from django.conf import settings
__author__ = 'Luis'
User = get_user_model()


def create_special_user(model_class, username):
    """
    This method is the default for creating a user and will invoke the model manager's
    get_or_create method. Defining a custom manager for a model with different fields,
    identifier field, and required fields implies defining a function to replace this
    one, for this one becomes useless.

    This function should not set the is_superuser field (i.e. it must be False) and
    should not set the password.

    Side note: yes, i know i could use a lambda but i wanted to doc this function.
    """
    return model_class.objects.get_or_create(username=username, defaults={'email': unicode(username) + u'@example.com'})
user_creator = getattr(settings, 'DETENTION_USER_CREATOR', create_special_user)