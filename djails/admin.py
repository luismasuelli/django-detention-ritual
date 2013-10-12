__author__ = 'Luis'
from django.contrib.admin import site, ModelAdmin
from models import ActiveBan, DeadBan


class ActiveBanAdmin(ModelAdmin):

    list_display = ['id', 'dictated_to', 'dictated_by', 'duration',
                    'dictation_reason', 'dictation_on', 'start_on']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None


class DeadBanAdmin(ModelAdmin):

    list_display = ['id', 'dictated_to', 'dictated_by', 'duration',
                    'dictation_reason', 'dictation_on', 'start_on',
                    'death_on', 'death_by', 'death_type', 'death_reason']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None


site.register(ActiveBan, ActiveBanAdmin)
site.register(DeadBan, DeadBanAdmin)