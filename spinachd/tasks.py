from importlib import import_module
from logging import getLogger
from typing import List

from django.apps import apps
from django.conf import settings
from django.core.mail import get_connection
from spinach import Tasks

from .settings import (
    SPINACH_ACTUAL_EMAIL_BACKEND,
    SPINACH_CLEAR_SESSIONS_PERIODICITY as PERIODICITY
)

tasks = Tasks()
logger = getLogger(__name__)


@tasks.task(name='spinachd:send_emails')
def send_emails(messages: List[str]):
    from .mail import deserialize_email_messages
    messages = deserialize_email_messages(messages)
    connection = get_connection(SPINACH_ACTUAL_EMAIL_BACKEND)
    logger.info('Sending %d emails using %s', len(messages),
                SPINACH_ACTUAL_EMAIL_BACKEND)
    connection.send_messages(messages)


@tasks.task(name='spinachd:clear_expired_sessions', periodicity=PERIODICITY)
def clear_expired_sessions():
    if not apps.is_installed('django.contrib.sessions'):
        logger.info('django.contrib.sessions not installed, '
                    'not clearing expired sessions')
        return

    engine = import_module(settings.SESSION_ENGINE)
    try:
        engine.SessionStore.clear_expired()
    except NotImplementedError:
        logger.info("Session engine '%s' doesn't support clearing "
                    "expired sessions", settings.SESSION_ENGINE)
