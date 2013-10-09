from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
import service

__author__ = 'Luis'


def istuple(value, n):
    return isinstance(value, tuple) and len(value) == n


class ifban(object):

    def __init__(self, allow_anonymous, param_name='current_ban', service_attr_name='service'):
        self.allow_anonymous = allow_anonymous
        self.param_name = param_name
        self.service_attr_name = service_attr_name

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
            return False, None
        #get the service from the user and call it.
        service_ = service.DjailsService(request.user)
        return service_.my_current_ban(), service_

    def _dispatch(self, view, args, kwargs):
        """
        Dispatches the view processing according to:
            1. (No auth app or No user logged in) & not "allowing" anonymous users: trigger on_anonymous.
            2. ((No auth app or No user logged in) & "allowing" anonymous users): trigger view.
            3. User is not banned: trigger view.
            4. User is banned: trigger on_banned.
        """
        result, service_ = self._get_ban(args[0])
        if result is False and not self.allow_anonymous:
            return self.on_anonymous(args[0], view, *args[1:], **kwargs)
        elif not result:
            setattr(args[0], self.service_attr_name, service_)
            return view(*args, **kwargs)
        else:
            setattr(args[0], self.service_attr_name, service_)
            kwargs[self.param_name] = result
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
        result = self.get_content(request, view, *args, **kwargs)
        if istuple(result, 2):
            content, content_type = result
        elif istuple(result, 1):
            content, content_type = result + ('text/plain',)
        elif isinstance(result, basestring):
            content, content_type = result, 'text/plain'
        else:
            raise TypeError("Response content must be a 1 or 2 items tuple, or a string type value")
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
        result = self.get_redirection(request, view, *args, **kwargs)
        if istuple(result, 2):
            target, permanent = result
        elif istuple(result, 1):
            target, permanent = result + (False,)
        elif isinstance(result, basestring):
            target, permanent = result, False
        else:
            raise TypeError("Redirection target must be a 1 or 2 items tuple, or a string type value")
        return redirect(target, permanent=permanent)

    def get_redirection(self, request, view, *args, **kwargs):
        """
        Must process the request, view, and ban parameter in **kwargs (as specified in base on_banned method) to
        yield the target url AND determine if it's a 302 or 301 redirection. Defaults to '/' and False in a
        (url, boolean) tuple, where True in the boolean means a permanent (301) redirection
        """
        return '/', False


class ifban_same(ifban):

    def on_banned(self, request, view, *args, **kwargs):
        """
        Calls the same view for both banned or unbanned user.
        The request will have an attribute as defined in the constructor for the service name.
        Your view must handle a ban parameter as defined in the decorator's name.
        """
        return view(request, *args, **kwargs)