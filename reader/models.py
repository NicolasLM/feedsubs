from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.db import models

from .validators import http_port_validator


class Feed(models.Model):
    name = models.CharField(max_length=100, unique=True)
    uri = models.URLField(
        unique=True,
        validators=[URLValidator(schemes=['http', 'https']),
                    http_port_validator]
    )
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    last_hash = models.BinaryField(max_length=20, null=True, blank=True)
    frequency_per_year = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return 'Feed {}: {}'.format(self.name, self.uri)


class Article(models.Model):
    id_in_feed = models.CharField(max_length=200)
    uri = models.URLField()
    title = models.TextField()
    content = models.TextField()
    published_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    feed = models.ForeignKey(Feed, models.CASCADE)

    class Meta:
        ordering = ('-published_at', '-created_at')

    def __str__(self):
        return 'Article {}: {}'.format(self.title, self.feed.name)


class ReaderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='reader_profile')
    feeds = models.ManyToManyField(Feed, related_name='subscribers', blank=True)
    stars = models.ManyToManyField(Article, related_name='stared_by',
                                   blank=True)
    read = models.ManyToManyField(Article, related_name='read_by', blank=True)

    def __str__(self):
        return 'ReadProfile of {}'.format(self.user)
