from django import VERSION
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.contrib.auth import get_user_model
import service
if VERSION[:2] < (1, 5):
    raise ImproperlyConfigured("Django 1.5 is required for djails application to work")
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


#We assure those properties exist since we need both a model method and a cache
#    property to check user bans.
djails_property = getattr(settings, 'DJAILS_USER_MODEL_BAN_SERVICE_PROPERTY', 'djails_service')
djails_cache = getattr(settings, 'DJAILS_USER_MODEL_BAN_SERVICE_CACHE_PROPERTY', '_' + djails_property)
djails_creator = getattr(settings, 'DJAILS_SPECIAL_USER_CREATE_FUNCTION', create_special_user)
djails_ban_param = getattr(settings, 'DJAILS_CURRENT_BAN_VIEW_PARAMETER_NAME', 'current_ban')


#This code extends the current User model to provide the ban service.
def get_ban_service(self):
    if not hasattr(self, djails_cache):
        setattr(self, djails_cache, service.DjailsService(self))
    return getattr(self, djails_cache)
setattr(User, djails_property, property(get_ban_service))