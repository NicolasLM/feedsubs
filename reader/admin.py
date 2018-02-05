from django.contrib import admin

from . import models
from .tasks import tasks


@admin.register(models.Feed)
class FeedAdmin(admin.ModelAdmin):

    actions = ['sync']

    def sync(self, request, queryset):
        for feed in queryset:
            tasks.schedule('synchronize_feed', str(feed.id))

    sync.short_description = 'Synchronize feed'


@admin.register(models.Article)
class ArticleAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ReaderProfile)
class ProfileAdmin(admin.ModelAdmin):
    pass
