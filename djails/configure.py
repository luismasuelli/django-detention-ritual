from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import UserManager
import service
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
    return model_class.objects.get_or_create(username=username, defaults={'email': unicode(username) + u'@special.com'})


if not settings.configured:
    settings.configure(DJAILS_INSTALLED=True)
else:
    settings.DJAILS_INSTALLED = True

#We assure those properties exist since we need both a model method and a cache
#    property to check user bans.
if not getattr(settings, 'DJAILS_USER_MODEL_BAN_SERVICE_PROPERTY', None):
    settings.DJAILS_USER_MODEL_BAN_SERVICE_PROPERTY = 'djails_service'
if not getattr(settings, 'DJAILS_USER_MODEL_BAN_SERVICE_CACHE_PROPERTY', None):
    settings.DJAILS_USER_MODEL_BAN_SERVICE_CACHE_PROPERTY = '_' + settings.DJAILS_USER_MODEL_BAN_SERVICE_PROPERTY
if not getattr(settings, 'DJAILS_SPECIAL_USER_CREATE_FUNCTION', None):
    settings.DJAILS_SPECIAL_USER_CREATE_FUNCTION = create_special_user

#This code extends the current User model to provide the ban service.
def ban_service(self):
    if not hasattr(self, settings.DJAILS_USER_MODEL_BAN_SERVICE_CACHE_PROPERTY):
        setattr(self, settings.DJAILS_USER_MODEL_BAN_SERVICE_CACHE_PROPERTY, service.DjailsService(self))
    return getattr(self, settings.DJAILS_USER_MODEL_BAN_SERVICE_CACHE_PROPERTY)
setattr(User, settings.DJAILS_USER_MODEL_BAN_SERVICE_PROPERTY, property(ban_service))