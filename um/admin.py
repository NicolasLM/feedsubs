import pprint

from django.contrib import admin
from django.contrib.sessions.models import Session

from . import models


@admin.register(models.UMProfile)
class ProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):

    def _session_data(self, obj):
        return pprint.pformat(obj.get_decoded())

    _session_data.allow_tags = True
    list_display = ['session_key', '_session_data', 'expire_date']
    readonly_fields = ['session_key', '_session_data']
    exclude = ['session_data']
