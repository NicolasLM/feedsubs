from typing import Optional
from urllib.parse import urlsplit
from uuid import uuid4

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from django.db import models
from django.urls import reverse
from django.template.defaultfilters import filesizeformat

from .validators import http_port_validator


URI_MAX_LENGTH = 2048  # https://stackoverflow.com/a/417184


class Feed(models.Model):
    name = models.CharField(max_length=100)
    uri = models.URLField(
        max_length=URI_MAX_LENGTH,
        unique=True,
        validators=[URLValidator(schemes=['http', 'https']),
                    http_port_validator]
    )
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    last_hash = models.BinaryField(max_length=20, null=True, blank=True)
    last_failure = models.TextField(blank=True, null=False)
    frequency_per_year = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)

    @property
    def domain(self):
        domain = urlsplit(self.uri).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    def __str__(self):
        return 'Feed {}: {}'.format(self.name, self.uri)


class Article(models.Model):
    id_in_feed = models.CharField(max_length=400)
    uri = models.URLField(max_length=URI_MAX_LENGTH, blank=True, null=False)
    title = models.TextField(blank=True, null=False)
    content = models.TextField(blank=True, null=False)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    feed = models.ForeignKey(Feed, models.CASCADE)

    class Meta:
        ordering = ('-published_at', '-created_at')
        unique_together = (('feed', 'id_in_feed'),)

    def __str__(self):
        return 'Article {}: {}'.format(self.title, self.feed.name)


class Attachment(models.Model):
    uri = models.URLField(max_length=URI_MAX_LENGTH)
    title = models.TextField(blank=True, null=False)
    mime_type = models.CharField(max_length=100, blank=True, null=False)
    size_in_bytes = models.PositiveIntegerField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)

    article = models.ForeignKey(Article, models.CASCADE)

    @property
    def simple_type(self) -> Optional[str]:
        if not self.mime_type:
            return None

        return self.mime_type.split('/')[0]

    def __str__(self):
        rv = self.title
        if self.size_in_bytes:
            rv += ' - {}'.format(filesizeformat(self.size_in_bytes))
        if self.duration:
            rv += ' - {}'.format(self.duration)
        return rv


class ReaderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='reader_profile')
    feeds = models.ManyToManyField(Feed, related_name='subscribers', blank=True,
                                   through='Subscription')
    stars = models.ManyToManyField(Article, related_name='stared_by',
                                   blank=True)
    read = models.ManyToManyField(Article, related_name='read_by', blank=True)

    def __str__(self):
        return 'ReadProfile of {}'.format(self.user)


class Subscription(models.Model):
    reader = models.ForeignKey(ReaderProfile, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    tags = ArrayField(
        models.CharField(max_length=40, blank=False, null=False),
        default=list,
        blank=True,
        null=False,
        size=100,
    )

    class Meta:
        unique_together = ('reader', 'feed')


class Board(models.Model):
    name = models.CharField(max_length=100)
    reader = models.ForeignKey(ReaderProfile, on_delete=models.CASCADE)
    tags = ArrayField(
        models.CharField(max_length=40, blank=False, null=False),
        default=list,
        blank=True,
        null=False,
        size=100,
    )

    is_static = False

    class Meta:
        unique_together = (('name', 'reader'),)

    def get_absolute_url(self):
        return reverse('reader:board-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class CachedImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    uri = models.URLField(max_length=URI_MAX_LENGTH, db_index=True, unique=True)
    format = models.CharField(max_length=8, blank=True, editable=False,
                              default='')
    width = models.PositiveSmallIntegerField(editable=False, default=0)
    height = models.PositiveSmallIntegerField(editable=False, default=0)
    size_in_bytes = models.PositiveIntegerField(editable=False, default=0)
    failure_reason = models.CharField(max_length=100, blank=True,
                                      editable=False, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if not self.format:
            return 'Failed image {}'.format(self.id)

        return 'Cached image {}'.format(self.id)

    @property
    def image_path(self):
        """Generate a hierarchy of folders to store an image based on its UUID.

        This prevents having a single directory with millions of entries, which
        file systems usually don't really like.
        """
        uuid_str = str(self.id)
        return 'cached-images/{}/{}/{}.{}'.format(
            uuid_str[:2],
            uuid_str[:4],
            uuid_str,
            self.format.lower()
        )

    @property
    def external_uri(self) -> Optional[str]:
        if self.failure_reason:
            return None

        return default_storage.url(self.image_path)

    def image_tag(self):
        from django.utils.safestring import mark_safe
        external_uri = self.external_uri
        if external_uri is None:
            return 'No preview'

        return mark_safe('<img src="{}" width="{}" height="{}">'.format(
            external_uri, self.width, self.height
        ))

    @property
    def resolution(self):
        return '{}x{}'.format(self.width, self.height)

    @property
    def is_tracking_pixel(self):
        return self.failure_reason == 'Tracking pixel'
