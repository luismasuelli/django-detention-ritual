from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from djails.models import ActiveBan, DeadBan, clean_duration, SPECIAL_USER_EXPIRER, SPECIAL_USER_CHECKER
from django.utils.timezone import now as tznow
from django.contrib.auth import get_user_model
__author__ = 'Luis'


User = get_user_model()


def add_ban(banner, banned, duration, reason):
    active_ban = ActiveBan()
    active_ban.dictation_on = tznow()
    active_ban.dictated_by = banner
    active_ban.dictated_to = banned
    active_ban.duration = duration
    active_ban.dictation_reason = reason
    active_ban.start_on = None
    active_ban.save()
    return active_ban


def _terminate_ban(unbanner, ban, when, reason, type_):
    dead_ban = DeadBan().copy_from(ban)
    dead_ban.start_on = ban.start_on
    dead_ban.death_on = when
    dead_ban.death_by = unbanner
    dead_ban.death_type = type_
    dead_ban.death_reason = reason
    ban.delete()
    dead_ban.save()
    return dead_ban


def expire_ban(expirer, ban, when):
    return _terminate_ban(expirer, ban, when, "** expired **", "E")


def forgive_ban(forgiver, ban, when, reason):
    user = ban.dictated_to
    dead_ban = _terminate_ban(forgiver, ban, when, reason, "F")
    _ensure_ban_with_start_date(user, when)
    return dead_ban


def revert_ban(reverter, ban, when, reason):
    user = ban.dictated_to
    dead_ban = _terminate_ban(reverter, ban, when, reason, "R")
    _ensure_ban_with_start_date(user, when)
    return dead_ban


def error_ban(reverter, ban, when, reason):
    return _terminate_ban(reverter, ban, when, reason, "I")


#These functions check the bans and revert them when errors occur.


def _check_ban_dictation_on_before(current_ban, now_, checker):
    if now_ < current_ban.dictation_on:
        error_ban(checker, current_ban,
                  now_, "** dictation-date-in-future[%s] **" %
                        (unicode(current_ban.dictation_on),))
        return True
    return False


def _check_ban_start_on_before(current_ban, now_, checker):
    if now_ < current_ban.start_on:
        error_ban(checker, current_ban,
                  now_, "** start-date-in-future[%s] **" %
                        (unicode(current_ban.start_on),))
        return True
    return False


def _check_ban_duration(current_ban, now_, checker):
    try:
        #Check if this ban must end or not.
        return clean_duration(current_ban.duration)
    except ValidationError:
        #Error due to a malformed duration string. This ban must
        #    be marked for termination for that reason.
        error_ban(checker, current_ban,
                  now_, "** malformed-duration[%s] **" %
                        (current_ban.duration,))
        return False


def _ensure_ban_with_start_date(user, default_date):
    qs = ActiveBan.objects.filter(dictated_to=user)
    qs_start_on = qs.filter(start_on__isnull=False)
    if qs.count() > 0 and qs_start_on.count() == 0:
        obj = qs.order_by("dictation_on")[0]
        obj.start_on = default_date or obj.dictation_on
        obj.save()


def _special_bancheck_users():
    return (User.objects.get(username=SPECIAL_USER_EXPIRER),
            User.objects.get(username=SPECIAL_USER_CHECKER))


def check_ban_for(banned):
    """
    Infinite loop - checks and expires bans to determine if
        target user is currently banned or not.

    Since this' an on-demand check, we don't need libraries such
        as "Celery" or "Kronos" to depend of. Moreover: implementing
        these checks in the admin are as straightforward as checking
        this in a method (perhaps using this function as a method in
        a user model).
    """

    expirer, checker = _special_bancheck_users()
    now_ = tznow()
    _check_dictation_date = lambda b: _check_ban_dictation_on_before(b, now_, checker)
    _check_start_date = lambda b: _check_ban_start_on_before(b, now_, checker)
    _check_duration = lambda b: _check_ban_duration(b, now_, checker)
    _active = lambda u: ActiveBan.objects.filter(dictated_to=u)
    _active_started = lambda u: _active(u).filter(start_on__isnull=False)
    _expected_end = lambda d, i: d + i if i is not None else None
    previous_start_on = None

    while True:
        #Verify at least one ban exists - if it doesn't, return None.
        #This check MUST occur in the context of a transaction, that's why we call
        #    select_for_update() before the count().
        if not _active(banned).select_for_update().count():
            #User is not banned because it has not any active ban.
            return None

        #Ensure at least one element has a start_on date.
        _ensure_ban_with_start_date(banned, previous_start_on)

        #Get the first ban with start_on
        current_ban = _active_started(banned).order_by("start_on")[0]
        delta = _check_duration(current_ban)

        #Assure delta is good, dictation_on and start_on are not in the future.
        if  delta is False or \
            _check_dictation_date(current_ban) or \
            _check_start_date(current_ban):
            continue

        #calculate expected end
        expected_end = _expected_end(current_ban.start_on, delta)

        if expected_end is None or now_ < expected_end:
            #User is banned because it has not an ending limit.
            #OR User is banned because it has a date beyond the current date.
            return current_ban
        elif now_ >= expected_end:
            #This ban must be marked as expired.
            expire_ban(expirer, current_ban, expected_end)
            #AND we must simulate the real-time expiration by
            #    assigning the last end as the new start.
            previous_start_on = expected_end
            #AND the loop shall continue.