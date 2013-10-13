# Create your views here.
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from detention import decorators, service, signals
from django.shortcuts import render_to_response
from django.template import loader
from detention.decorators import ifban_same
from django.dispatch import receiver
from django.core import serializers


class ifban_sample(decorators.ifban):

    def on_banned(self, request, *args, **kwargs):
        return render_to_response('example/banned-details.html', {'ban': request.current_ban})

    def on_anonymous(self, request, *args, **kwargs):
        return noauth_view(request)


class ifban_redirect_sample(decorators.ifban_redirect):

    def get_redirection(self, request, *args, **kwargs):
        return reverse('banned-target'), False

    def on_anonymous(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('noauth-target'))


class ifban_forbid_sample(decorators.ifban_forbid):

    def get_content(self, request, *args, **kwargs):
        return loader.render_to_string('example/forbidden.html'), 'text/html'

    def on_anonymous(self, request, *args, **kwargs):
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
                               'service': request.service,
                               'ban': request.current_ban})


@receiver(signals.ban_applied, dispatch_uid="example.ban_applied")
def user_ban_applied(sender, **kwargs):
    ban = kwargs['new_ban']
    with open("bans.log", "a") as f:
        f.write("created ban: %s" % serializers.serialize("json", [ban]))


@receiver(signals.ban_terminated, dispatch_uid="example.ban_terminated")
def user_ban_terminated(sender, **kwargs):
    ban = kwargs['ban']
    with open("bans.log", "a") as f:
        f.write("terminated ban: %s" % serializers.serialize("json", [ban]))


@receiver(signals.bans_expired, dispatch_uid="example.unbanned")
def user_unbanned(sender, **kwargs):
    ban = kwargs['current_ban']
    bans = kwargs['ban_list']
    with open("bans.log", "a") as f:
        f.write("user unbanned: %s. forgiven bans: %s" % (sender.username, serializers.serialize("json", bans)))