from django.core.management.base import BaseCommand

from ... import models, tasks
from ...html_processing import find_images_in_article


class Command(BaseCommand):
    help = 'Cache images found in all articles'

    def handle(self, *args, **options):
        chunk_size = 200
        images_uris = set()
        articles_iter = (
            models.Article.objects
            .select_related('feed')
            .iterator(chunk_size=chunk_size)
        )
        for i, article in enumerate(articles_iter, 1):
            images_uris.update(
                find_images_in_article(article.content, article.feed.uri)
            )
            if i % chunk_size == 0:
                tasks.cache_images(images_uris)
                images_uris = set()
