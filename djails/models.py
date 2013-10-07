from __future__ import unicode_literals
import re
import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


User = get_user_model()
_DURATION_RX = re.compile(r'^\s*((\d+)w)?\s*((\d+)d)?\s*((\d+)h)?\s*((\d+)m)?\s*((\d+)s)?\s*$', re.IGNORECASE)


SPECIAL_USER_EXPIRER = "__ban_expirer__"
SPECIAL_USER_AUTOBAN = "__ban_autoban__"
SPECIAL_USER_CHECKER = "__ban_checker__"
SPECIAL_USERS = [SPECIAL_USER_AUTOBAN, SPECIAL_USER_EXPIRER, SPECIAL_USER_CHECKER]


def clean_duration(dur):
    """
    Transforms a duration string to a timedelta.
    """

    match = _DURATION_RX.match(dur)
    if match is None:
        raise ValidationError(_('Invalid duration. Expected format: <A>w <B>d <C>h <D>m <E>s '
                                'specifying weeks, days, hours, minutes, seconds. Specifying none'
                                'of them implies an infinite duration'), code="DURATION_STRING")
    interval = []
    for i, g in enumerate(match.groups()):
        if i % 2:
            try:
                interval.append(int(g))
            except (TypeError, ValueError):
                interval.append(0)
    if sum(interval):
        return datetime.timedelta(weeks=interval[0], days=interval[1],
                                  hours=interval[2], minutes=interval[3],
                                  seconds=interval[4])
    else:
        return None


class BanDataManager(models.Manager):
    """
    Erroneous entities are filtered by the manager (i.e. entities with no associated Active/Dead
    Ban entries - or both type of entries associated - are not retrieved).
    """

    def get_query_set(self):
        return super(BanDataManager, self).get_query_set().filter(Q(activeban__isnull=False, deadban__isnull=True) |
                                                                  Q(activeban__isnull=True, deadban__isnull=False))


class BanData(models.Model):
    """
    Ban data: first-level ban data (when was it created, by whom, to whom, reason, duration).
    This exists in it's own entity to track the data and the current state.

    Erroneous entities are filtered by the manager (i.e. entities with no associated Active/Dead
    Ban entries - or both type of entries associated - are not retrieved).
    """

    objects = BanDataManager()

    dictation_on = models.DateTimeField(null=False, editable=False, db_index=True, verbose_name=_("Ban creation date"))
    dictation_reason = models.TextField(null=False, max_length=1024, verbose_name=_("Ban reason"))
    duration = models.CharField(null=False, max_length=255, validators=[clean_duration], verbose_name=_("Ban duration"))
    dictated_to = models.ForeignKey(User, related_name="+", null=False, editable=False, verbose_name=_("Ban target"))
    dictated_by = models.ForeignKey(User, related_name="+", null=False, editable=False,verbose_name=_("Ban dictator"))

    def copy_from(self, ban):
        self.dictation_on = ban.dictation_on
        self.dictation_reason = ban.dictation_reason
        self.duration = ban.duration
        self.dictated_by = ban.dictated_by
        self.dictated_to = ban.dictated_to
        return self


class ActiveBanMixIn(models.Model):
    """
    Activa Ban Mix-in: tracks the ban's start date.
    """

    start_on = models.DateTimeField(null=True, editable=False, db_index=True, verbose_name=_("Ban start date"))

    class Meta:
        abstract = True


class DeadBanMixin(ActiveBanMixIn):
    """
    Dead Ban Mix-in: tracks ending data for the ban (and the active data as well).
    """

    DEATH_CHOICES = (
        ("E", _("Expired")),
        ("F", _("Forgiven")),
        ("R", _("Reverted")),
        ("I", _("Internal Error"))
    )

    death_on = models.DateTimeField(null=False, editable=False, db_index=True, verbose_name=_("Termination time"))
    death_by = models.ForeignKey(User, related_name="+", null=False, editable=False, verbose_name=_("Terminator"))
    death_reason = models.TextField(null=False, max_length=1024, verbose_name=_("Termination reason"))
    death_type = models.CharField(null=False, max_length=1, choices=DEATH_CHOICES, verbose_name=_("Termination type"))

    class Meta:
        abstract = True


class ActiveBan(BanData, ActiveBanMixIn):
    """
    Active Ban - implements the mix-in and links to BanData to get the generic data.
    """

    class Meta:
        verbose_name = _("Active Ban")
        verbose_name_plural = _("Active Bans")


class DeadBan(BanData, DeadBanMixin):
    """
    Dead Ban - implements the mix-in and links to BanData to get the generic data.
    """

    class Meta:
        verbose_name = _("Dead Ban")
        verbose_name_plural = _("Dead Bans")


