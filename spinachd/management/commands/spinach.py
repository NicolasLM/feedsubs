import copy
import signal

from django.core.management.base import BaseCommand
try:
    from raven.contrib.django.models import client as raven_client
except ImportError:
    raven_client = None
from spinach.contrib.sentry import register_sentry

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

        if raven_client is not None:
            register_sentry(raven_client, spin.namespace)

        kwargs = copy.copy(SPINACH_WORKER)
        if options['queue']:
            kwargs['queue'] = options['queue']

        def handle_sigterm(*args):
            raise KeyboardInterrupt()

        signal.signal(signal.SIGTERM, handle_sigterm)

        spin.start_workers(**kwargs)
