import logging.config

from django.conf import settings
from django.core.management.base import BaseCommand
from waitress import serve


class Command(BaseCommand):
    help = 'Run waitress'

    def handle(self, *args, **options):
        from feedsubs.wsgi import application

        if settings.LOGGING_CONFIG is None:
            logging.config.dictConfig(settings.LOGGING)

        serve(application, **getattr(settings, 'WAITRESS', {}))
