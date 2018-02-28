import importlib

from django.apps import AppConfig
from django.utils.module_loading import module_has_submodule
from spinach import Tasks, Engine

from .settings import SPINACH_ENGINE

spin = Engine(**SPINACH_ENGINE)


class SpinachdConfig(AppConfig):
    name = 'spinachd'

    def ready(self):
        from . import signals  # noqa

        for discovered_module in autodiscover_modules('tasks'):
            try:
                module_tasks = discovered_module.tasks
            except AttributeError:
                continue

            if isinstance(module_tasks, Tasks):
                spin.attach_tasks(module_tasks)


def autodiscover_modules(*args):
    from django.apps import apps

    imported_modules = list()
    for app_config in apps.get_app_configs():
        for module_to_search in args:
            # Attempt to import the app's module.
            try:
                path = '%s.%s' % (app_config.name, module_to_search)
                imported_modules.append(importlib.import_module(path))
            except Exception:
                # Decide whether to bubble up this error. If the app just
                # doesn't have the module in question, we can ignore the error
                # attempting to import it, otherwise we want it to bubble up.
                if module_has_submodule(app_config.module, module_to_search):
                    raise

    return imported_modules
