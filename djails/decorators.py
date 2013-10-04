from functools import wraps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.http.response import HttpResponse, HttpResponsePermanentRedirect

__author__ = 'Luis'
ban_param = settings.DJAILS_CURRENT_BAN_VIEW_PARAMETER_NAME
ban_property = settings.DJAILS_USER_MODEL_BAN_SERVICE_PROPERTY


class ifban(object):

    def __init__(self, allow_anonymous):
        self.allow_anonymous = allow_anonymous

    def on_anonymous(self, request, view, *args, **kwargs):
        """
        This method must be defined to define what to do if a request comes to this view and no user is logged in or
        the "auth" app is not installed. The following params must be specified:
        1. 2 (two) positional parameters.
           a. the current request.
           b. the original wrapped view.
        2. *args and **kwargs as they will serve to generic purposes.

        It must return a response as any view would do.
        """
        raise NotImplementedError()

    def on_banned(self, request, view, *args, **kwargs):
        """
        What to do when the user is banned. The following params must be specified:
        1. 2 (two) positional parameters.
           a. the current request.
           b. the original wrapped view.
        2. *args and **kwargs as they will serve to generic purposes. Remember that in the **kwargs there will be
           a param whose name will be the value of DJAILS_CURRENT_BAN_VIEW_PARAMETER_NAME system setting (by default
           it will be 'current_ban') which will hold the current ban for the user.

        It must return a response as any view would do.
        """
        return NotImplementedError()

    def _get_ban(self, request):
        """
        Checks the ban for the logged user in a request and returns a result:
            None: there's no ban for the logged user (i.e. it's not banned).
            <ban>: there's a ban for the logged user (i.e. it's banned).
            False: there's no user logged in or the request has no "user" attribute (i.e. "auth" app isn't installed).
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated():
            #the auth application is not installed or the user is not authenticated
            return False
        #get the service from the user and call it.
        #if it does not exist, that's a strange error to worry about.
        service = getattr(request.user, ban_property, None)
        if service:
            return service.my_current_ban()
        else:
            raise RuntimeError(
                "The specified ban service property '%s' cannot be accesed for a '%s' object!" %
                (ban_property, request.user.__class__.__name__)
            )

    def _dispatch(self, view, args, kwargs):
        """
        Dispatches the view processing according to:
            1. (No auth app or No user logged in) & not "allowing" anonymous users: trigger on_anonymous.
            2. ((No auth app or No user logged in) & "allowing" anonymous users): trigger view.
            3. User is not banned: trigger view.
            4. User is banned: trigger on_banned.
        """
        result = self._get_ban(args[0])
        if result is False and not self.allow_anonymous:
            return self.on_anonymous(args[0], view, *args[1:], **kwargs)
        elif not result:
            return view(*args, **kwargs)
        else:
            kwargs[ban_param] = result
            return self.on_banned(args[0], view, *args[1:], **kwargs)

    def __call__(self, view):
        """
        Takes the current view and returns a wrapper that does the dispatch.
        """
        @wraps(view)
        def wrapper(*args, **kwargs):
            return self._dispatch(view, args, kwargs)
        return wrapper


class ifban_forbid(ifban):

    def on_banned(self, request, view, *args, **kwargs):
        """
        You should not redefine this method. This is a convenient method defined for you in this class.
        """
        content, content_type = self.get_content(request, view, *args, **kwargs)
        return HttpResponseForbidden(content=content, content_type=content_type)

    def get_content(self, request, view, *args, **kwargs):
        """
        Must process the request, view, and ban parameter in **kwargs (as specified in base on_banned method) to
        yield the content and content_type for the 403 response. Defaults to a void string and a 'text/plain' type
        in a (content, content_type) tuple.
        """
        return '', 'text/plain'


class ifban_redirect(ifban):

    def on_banned(self, request, view, *args, **kwargs):
        """
        You should not redefine this method. This is a convenient method defined for you in this class.
        """
        target, permanent = self.get_redirection(request, view, *args, **kwargs)
        if permanent:
            return HttpResponsePermanentRedirect(target)
        else:
            return HttpResponseRedirect(target)

    def get_redirection(self, request, view, *args, **kwargs):
        """
        Must process the request, view, and ban parameter in **kwargs (as specified in base on_banned method) to
        yield the target url AND determine if it's a 302 or 301 redirection. Defaults to '/' and False in a
        (url, boolean) tuple, where True in the boolean means a permanent (301) redirection
        """
        return '/', False