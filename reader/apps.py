from django.apps import AppConfig


class ReaderConfig(AppConfig):
    name = 'reader'

    def ready(self):
        from . import signals  # noqa
