from django.db import reset_queries, close_old_connections
from spinach import signals

try:
    from raven.contrib.django.models import client as raven_client
except ImportError:
    raven_client = None

from .apps import spin


@signals.job_started.connect_via(spin.namespace)
def job_started(*args, job=None, **kwargs):
    reset_queries()
    close_old_connections()
    if raven_client is not None:
        raven_client.context.activate()
        raven_client.transaction.push(job.task_name)


@signals.job_finished.connect_via(spin.namespace)
def job_finished(*args, job=None, **kwargs):
    close_old_connections()
    if raven_client is not None:
        raven_client.transaction.push(job.task_name)
        raven_client.context.clear()


@signals.job_failed.connect_via(spin.namespace)
def job_failed(*args, job=None, **kwargs):
    if raven_client is not None:
        raven_client.captureException(
            extra={attr: getattr(job, attr) for attr in job.__slots__}
        )
