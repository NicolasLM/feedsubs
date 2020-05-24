from django.conf import settings


READER_CACHE_IMAGES = getattr(settings, 'READER_CACHE_IMAGES', False)
