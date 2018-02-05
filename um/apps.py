from django.apps import AppConfig


class UMConfig(AppConfig):
    name = 'um'

    def ready(self):
        from . import signals  # noqa
