import pkg_resources

from .base import *


# Production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# Proxy requirements for these settings to work:
# - Provide SSL termination
# - Redirect HTTP -> HTTPS
# - Redirect www. -> naked domain
# - Clean and insert X-Forwarded-Proto in requests
# - Append an X-Forwarded-For IP in requests
# - Add all standard security headers to responses

INSTALLED_APPS += [
    'raven.contrib.django',
    'waitressd.apps.WaitressdConfig'
]
MIDDLEWARE = (
        ['xff.middleware.XForwardedForMiddleware'] +
        ['waitressd.middleware.access_log'] +
        MIDDLEWARE +
        ['raven.contrib.django.middleware.SentryResponseErrorIdMiddleware']
)

STATIC_ROOT = '/opt/static'
ALLOWED_HOSTS = [config('ALLOWED_HOST', default='feedsubs.com')]

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('X-Forwarded-Proto', 'https')
XFF_TRUSTED_PROXY_DEPTH = 1
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

ADMINS = [('Nicolas', 'nicolas@lemanchet.fr')]
MANAGERS = [('Nicolas', 'nicolas@lemanchet.fr')]
DEFAULT_FROM_EMAIL = 'hello@feedsubs.com'
EMAIL_BACKEND = 'spinachd.mail.BackgroundEmailBackend'
SERVER_EMAIL = 'hello@feedsubs.com'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 2525
EMAIL_HOST_USER = 'hello@feedsubs.com'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 120

RAVEN_CONFIG = {
    'dsn': config('SENTRY_DSN'),
    'release': pkg_resources.require("feedsubs")[0].version,
}

CACHES = {
    'default': {
        'TIMEOUT': 24 * 60 * 60,  # keys expire by default after 1 day
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_CACHE_URL', default='redis://'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'IGNORE_EXCEPTIONS': True,
        }
    }
}
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True

WAITRESS = {
    'port': config('WAITRESS_PORT', default=8000, cast=int),
    'asyncore_use_poll': True,
    'threads': config('WAITRESS_THREADS', default=16, cast=int)
}
