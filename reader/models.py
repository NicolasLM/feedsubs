from django.contrib.auth.models import User
from django.db import models


class Feed(models.Model):
    name = models.CharField(max_length=100, unique=True)
    uri = models.URLField(unique=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    last_hash = models.BinaryField(max_length=20, null=True, blank=True)

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


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    feeds = models.ManyToManyField(Feed, related_name='subscribers', blank=True)
    stars = models.ManyToManyField(Article, related_name='stared_by',
                                   blank=True)
    read = models.ManyToManyField(Article, related_name='read_by', blank=True)
    night_mode = models.BooleanField(default=False)
    deletion_pending = models.BooleanField(default=False)

    def __str__(self):
        return 'Profile of {}'.format(self.user)
