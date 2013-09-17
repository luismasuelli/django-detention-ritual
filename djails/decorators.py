from functools import wraps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden

__author__ = 'Luis'
ban_param = settings.DJAILS_CURRENT_BAN_VIEW_PARAMETER_NAME


def _ban(request):
    """
    Checks if a logged user is banned or not.
        None: not banned
        <ban>: banned
        False: not logged or auth app not installed
    """

    if not hasattr(request, 'user') or not request.user.is_authenticated():
        #the auth application is not installed or the user is not authenticated
        return False
    #get the bound method from the user and call it. if the method does not exist, True value is returned
    service = getattr(request.user, settings.DJAILS_USER_MODEL_BAN_SERVICE_PROPERTY, None)
    if service:
        return service.my_current_ban()


def good_child_decorator(on_banned, on_anonymous=None):
    """
    Decorator that tests if the current user is banned or not.
    Two params are accepted by this decorator:
        1. Callback to execute when the user is banned.
           This callback must return a response.
           It will be executed instead of the view function.
        2. Optional callback to execute if the app is not installed or the user is not authenticcated.
           This callback must return a response.
           If not specified, normal page processing will occur.
               In such case, you should ensure manually (via login decorator) if you want to check if the user is authenticated.
           Otherwise, it will be executed instead of the view function.
    """

    def _decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = _ban(args[0])
            if result is False and (on_anonymous is not None):
                return on_anonymous(args[0], func, *args[1:], **kwargs)
            elif not result:
                return func(*args, **kwargs)
            else:
                kwargs[ban_param] = result
                return on_banned(args[0], func, *args[1:], **kwargs)
        return wrapper
    return _decorator


def good_child_or_redirect(target, on_anonymous=None):
    """
    Implements the previos decorator with a simple "redirect" function.

    The target can be a tuple (url_name, dict|tuple) - the target will be reversed.
        Otherwise, it will not be reolved.
    """

    if isinstance(target, tuple):
        if isinstance(target[1], dict):
            result = reverse(target[0], kwargs=target[1])
        else:
            result = reverse(target[0], args=target[1])
    else:
        result = target
    return good_child_decorator(
        lambda req, view, *args, **kwargs: HttpResponseRedirect(result),
        on_anonymous
    )


def good_child_or_forbid(content_func=lambda r, v, *a, **ka: {'content': '', 'content_type': 'text/plain'}, on_anonymous=None):
    """
    Implements the generic decorator with a (perhaps elaborated) "forbidden" function.

    A custom function can be passed to generate the 403 content and content_type by returning
        a dict with those keys (both keys should be included).
    """

    return good_child_decorator(
        lambda req, view, *args, **kwargs: HttpResponseForbidden(**content_func(req, view, *args, **kwargs)),
        on_anonymous
    )


def good_child_or_chain(target_view, on_anonymous=None):
    """
    Implements the generic decorator by giving an alternative url to render when the user is banned.

    If the user is banned, the target_view is rendered with the same parameters.
        The view must accept the request, the original view_function, *positionals, and **named.
    """

    return good_child_decorator(
        target_view,
        on_anonymous
    )