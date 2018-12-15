from django.contrib import admin
from spinach import Batch

from . import models
from .tasks import tasks


@admin.register(models.Feed)
class FeedAdmin(admin.ModelAdmin):

    list_display = ('name', 'domain', 'last_fetched_at', 'last_failure')
    actions = ['sync']

    def sync(self, request, queryset):
        batch = Batch()
        for feed in queryset:
            batch.schedule('synchronize_feed', feed.id, force=True)
        tasks.schedule_batch(batch)

    sync.short_description = 'Synchronize feed'


@admin.register(models.Article)
class ArticleAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'size_in_bytes', 'duration')
    readonly_fields = ('article',)


@admin.register(models.ReaderProfile)
class ProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Board)
class BoardAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CachedImage)
class CachedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'uri', 'format', 'resolution', 'is_tracking_pixel',
                    'created_at')
    readonly_fields = ('id', 'uri', 'format', 'resolution',
                       'size_in_bytes', 'failure_reason',
                       'created_at', 'image_tag')
