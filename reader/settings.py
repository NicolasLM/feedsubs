from django.conf import settings


READER_CACHE_IMAGES = getattr(settings, 'READER_CACHE_IMAGES', False)
READER_FEED_ARTICLE_THRESHOLD = getattr(settings, 'READER_FEED_ARTICLE_THRESHOLD', 20_000)
