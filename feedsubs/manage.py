#!/usr/bin/env python
import os
import sys

# This manage.py is not in the root of the repository like other Django
# projects to allow adding it to the feedsubs package to ship it as a wheel.


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "feedsubs.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
