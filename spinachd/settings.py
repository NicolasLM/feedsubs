from django.conf import settings
from spinach import RedisBroker

SPINACH_ENGINE = getattr(settings, 'SPINACH_ENGINE', {
    'broker': RedisBroker()
})

SPINACH_WORKER = getattr(settings, 'SPINACH_WORKER', {})
