# Create your views here.
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from djails import decorators, service
from django.shortcuts import render_to_response
from django.template import loader
from djails.decorators import ifban_same


class ifban_sample(decorators.ifban):

    def on_banned(self, request, view, *args, **kwargs):
        return render_to_response('example/banned-details.html', {'ban': kwargs['current_ban']})

    def on_anonymous(self, request, view, *args, **kwargs):
        return noauth_view(request)


class ifban_redirect_sample(decorators.ifban_redirect):

    def get_redirection(self, request, view, *args, **kwargs):
        return reverse('banned-target'), False

    def on_anonymous(self, request, view, *args, **kwargs):
        return HttpResponseRedirect(reverse('noauth-target'))


class ifban_forbid_sample(decorators.ifban_forbid):

    def get_content(self, request, view, *args, **kwargs):
        return loader.render_to_string('example/forbidden.html'), 'text/html'

    def on_anonymous(self, request, view, *args, **kwargs):
        return HttpResponseRedirect(reverse('noauth-target'))


def banned_view(request):
    return render_to_response('example/banned.html')


def noauth_view(request):
    return render_to_response('example/noauth.html')


@ifban_forbid_sample(False)
def view1(request):
    return render_to_response('example/view.html', {'x': 1})


@ifban_redirect_sample(False)
def view2(request):
    return render_to_response('example/view.html', {'x': 2})


@ifban_sample(False)
def view3(request):
    return render_to_response('example/view.html', {'x': 3})


@login_required
@ifban_same(allow_anonymous=True)
def profile(request, *args, **kwargs):
    return render_to_response('example/profile.html',
                              {'user': request.user,
                               'service': kwargs.get('service'),
                               'ban': kwargs.get('current_ban')})