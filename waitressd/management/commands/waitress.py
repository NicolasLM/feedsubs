import logging.config
import signal

from django.conf import settings
from django.core.management.base import BaseCommand
from waitress import serve


class Command(BaseCommand):
    help = 'Run waitress'

    def handle(self, *args, **options):
        from feedsubs.wsgi import application

        if settings.LOGGING_CONFIG is None:
            logging.config.dictConfig(settings.LOGGING)

        def handle_sigterm(*args):
            raise KeyboardInterrupt()

        signal.signal(signal.SIGTERM, handle_sigterm)

        serve(application, **getattr(settings, 'WAITRESS', {}))
