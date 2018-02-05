from django.contrib import admin

from . import models


@admin.register(models.UMProfile)
class ProfileAdmin(admin.ModelAdmin):
    pass
