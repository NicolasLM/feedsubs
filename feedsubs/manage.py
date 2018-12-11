#!/usr/bin/env python
import os
import sys

# This manage.py is not in the root of the repository like other Django
# projects to allow adding it to the feedsubs package to ship it as a wheel.


def main():

    if os.environ.get('DDTRACE_EXTRA_PATCH') == 'true':
        # The ddtrace/Django integration only patches Django internals, it
        # doesn't patch other libraries.
        # Manually patching them very early here seems like a less intrusive
        # approach than running the whole app under `ddtrace-run`
        import ddtrace
        ddtrace.patch(requests=True, botocore=True, redis=True)

    # Dirty Monkey Patch to prevent boto3 from creating many threadpools
    try:
        from boto3.s3 import transfer
    except ImportError:
        pass
    else:
        def create_transfer_manager(*arg, **kwargs):
            return transfer.TransferManager(
                *arg, **kwargs, executor_cls=transfer.NonThreadedExecutor
            )
        transfer.create_transfer_manager = create_transfer_manager

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
