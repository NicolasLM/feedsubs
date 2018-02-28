from django.contrib import admin
from spinach import Batch

from . import models
from .tasks import tasks


@admin.register(models.Feed)
class FeedAdmin(admin.ModelAdmin):

    actions = ['sync']

    def sync(self, request, queryset):
        batch = Batch()
        for feed in queryset:
            batch.schedule('synchronize_feed', str(feed.id))
        tasks.schedule_batch(batch)

    sync.short_description = 'Synchronize feed'


@admin.register(models.Article)
class ArticleAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ReaderProfile)
class ProfileAdmin(admin.ModelAdmin):
    pass
