import copy
import logging.config

from django.conf import settings
from django.core.management.base import BaseCommand

from ...apps import spin
from ...settings import SPINACH_WORKER


class Command(BaseCommand):
    help = 'Run spinach workers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            dest='queue',
            help='Queue to consume'
        )

    def handle(self, *args, **options):
        if settings.LOGGING_CONFIG is None:
            logging.config.dictConfig(settings.LOGGING)

        kwargs = copy.copy(SPINACH_WORKER)
        if options['queue']:
            kwargs['queue'] = options['queue']

        spin.start_workers(**kwargs)
