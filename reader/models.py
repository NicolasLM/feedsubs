from urllib.parse import urlsplit

from django.contrib.auth.models import User
from django.core.validators import URLValidator
from django.db import models
from django.contrib.postgres.fields import ArrayField

from .validators import http_port_validator


class Feed(models.Model):
    name = models.CharField(max_length=100)
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

    @property
    def domain(self):
        domain = urlsplit(self.uri).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    def __str__(self):
        return 'Feed {}: {}'.format(self.name, self.uri)


class Article(models.Model):
    id_in_feed = models.CharField(max_length=200)
    uri = models.URLField()
    title = models.TextField()
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
