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
    'waitressd.apps.WaitressdConfig'
]
MIDDLEWARE = (
    ['waitressd.middleware.access_log'] +
    ['whitenoise.middleware.WhiteNoiseMiddleware'] +
    MIDDLEWARE
)

STATIC_ROOT = '/opt/static'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

ALLOWED_HOSTS = [config('ALLOWED_HOST', default='feedsubs.com')]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('X-Forwarded-Proto', 'https')
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
    'ident': None,
    'threads': config('WAITRESS_THREADS', default=16, cast=int),
    'channel_timeout': config('WAITRESS_CHANNEL_TIMEOUT', default=60, cast=int),
    'connection_limit': config('WAITRESS_CONNECTION_LIMIT', default=100, cast=int),
    'trusted_proxy': '*',
    'trusted_proxy_count': 1,
    'trusted_proxy_headers': ['x-forwarded-for', 'x-forwarded-proto'],
    'clear_untrusted_proxy_headers': True
}

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_REGION_NAME = 'ams3'
AWS_S3_ENDPOINT_URL = 'https://ams3.digitaloceanspaces.com'
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'feedsubs'
AWS_DEFAULT_ACL = 'private'
AWS_QUERYSTRING_EXPIRE = 7800  # 2h10, must be more than article cache


from ddtrace import config as dc, tracer, patch_all

tracer.configure(
    hostname=config('DD_AGENT_HOSTNAME', default='localhost'),
    port=config('DD_AGENT_PORT', 8126, cast=int),
    enabled=True
)
dc.django['service_name'] = 'feedsubs'
dc.django['cache_service_name'] = 'feedsubs-cache'
dc.django['database_service_name_prefix'] = 'feedsubs-'
dc.django['instrument_databases'] = True
dc.django['instrument_caches'] = True
dc.django['trace_query_string'] = True
dc.django['analytics_enabled'] = True
tracer.set_tags({'env': 'prod'})
patch_all()


import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from spinach.contrib.sentry_sdk_spinach import SpinachIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    environment='prod',
    release=pkg_resources.require("feedsubs")[0].version,
    send_default_pii=True,
    integrations=[
        DjangoIntegration(),
        SpinachIntegration()
    ]
)
