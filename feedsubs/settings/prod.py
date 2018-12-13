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
    'ddtrace.contrib.django',
    'waitressd.apps.WaitressdConfig'
]
MIDDLEWARE = (
    ['xff.middleware.XForwardedForMiddleware'] +
    ['waitressd.middleware.access_log'] +
    ['whitenoise.middleware.WhiteNoiseMiddleware'] +
    MIDDLEWARE +
    ['raven.contrib.django.middleware.SentryResponseErrorIdMiddleware']
)

STATIC_ROOT = '/opt/static'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

ALLOWED_HOSTS = [config('ALLOWED_HOST', default='feedsubs.com')]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('X-Forwarded-Proto', 'https')
XFF_TRUSTED_PROXY_DEPTH = 1
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

ADMINS = [('Nicolas', 'nicolas@lemanchet.fr')]
MANAGERS = [('Nicolas', 'nicolas@lemanchet.fr')]
DEFAULT_FROM_EMAIL = 'info@feedsubs.com'
EMAIL_BACKEND = 'spinach.contrib.spinachd.mail.BackgroundEmailBackend'
SERVER_EMAIL = 'info@feedsubs.com'
EMAIL_HOST = 'smtp.eu.mailgun.org'
EMAIL_PORT = 2525
EMAIL_HOST_USER = 'info@feedsubs.com'
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
    'threads': config('WAITRESS_THREADS', default=16, cast=int),
    'channel_timeout': config('WAITRESS_CHANNEL_TIMEOUT', default=60, cast=int),
    'connection_limit': config('WAITRESS_CONNECTION_LIMIT', default=100, cast=int)
}

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_REGION_NAME = 'ams3'
AWS_S3_ENDPOINT_URL = 'https://ams3.digitaloceanspaces.com'
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'feedsubs'
AWS_DEFAULT_ACL = 'private'
AWS_QUERYSTRING_EXPIRE = 7800  # 2h10, must be more than article cache

DATADOG_TRACE = {
    'DEFAULT_SERVICE': 'feedsubs',
    'INSTRUMENT_CACHE': False,
    'TAGS': {'env': 'prod'},
    'AGENT_HOSTNAME': config('DD_AGENT_HOSTNAME', default='localhost'),
    'AGENT_PORT': config('DD_AGENT_PORT', 8126, cast=int),
}
