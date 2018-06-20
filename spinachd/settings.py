from django.conf import settings
from spinach import RedisBroker

SPINACH_ENGINE = getattr(settings, 'SPINACH_ENGINE', {
    'broker': RedisBroker()
})

SPINACH_WORKER = getattr(settings, 'SPINACH_WORKER', {})

SPINACH_ACTUAL_EMAIL_BACKEND = getattr(
    settings,
    'SPINACH_ACTUAL_EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)
