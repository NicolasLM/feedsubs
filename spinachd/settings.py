from django.conf import settings
from spinach import RedisBroker

SPINACH_SPIN = getattr(settings, 'SPINACH_SPIN', {
    'broker': RedisBroker()
})

SPINACH_WORKER = getattr(settings, 'SPINACH_WORKER', {})
