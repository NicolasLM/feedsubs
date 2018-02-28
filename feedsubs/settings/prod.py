import pkg_resources

from .base import *


# Production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# Proxy requirements for these settings to work:
# - Provide SSL termination
# - Redirect HTTP -> HTTPS
# - Redirect www. -> naked domain
# - Clean and insert X-Forwarded-Proto in requests
# - Clean and insert X-Forwarded-Host in requests
# - Clean and insert X-Forwarded-For in requests
# - Add all standard security headers to responses

INSTALLED_APPS += ['raven.contrib.django']
MIDDLEWARE = (
        ['xff.middleware.XForwardedForMiddleware'] +
        MIDDLEWARE +
        ['raven.contrib.django.middleware.SentryResponseErrorIdMiddleware']
)

STATIC_ROOT = '/opt/static'
ALLOWED_HOSTS = ['feedsubs.com']

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('X-Forwarded-Proto', 'https')
USE_X_FORWARDED_HOST = True


XFF_TRUSTED_PROXY_DEPTH = 1
XFF_STRICT = True

ADMINS = [('Nicolas', 'nicolas@lemanchet.fr')]
MANAGERS = [('Nicolas', 'nicolas@lemanchet.fr')]
DEFAULT_FROM_EMAIL = 'hello@feedsubs.com'
SERVER_EMAIL = 'hello@feedsubs.com'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'hello@feedsubs.com'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 120

RAVEN_CONFIG = {
    'dsn': config('SENTRY_DSN'),
    'release': pkg_resources.require("feedsubs")[0].version,
}
