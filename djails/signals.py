__author__ = 'Luis'

from django.core import signals
#the sender will be the banner user
ban_applied = signals.Signal(providing_args=["new_ban"])
ban_terminated = signals.Signal(providing_args=["ban"])
bans_expired = signals.Signal(providing_args=["current", "ban_list"])