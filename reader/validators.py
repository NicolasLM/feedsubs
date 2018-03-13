from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def http_port_validator(value):
    parsed = urlparse(value)
    if parsed.port not in (None, 80, 443):
        raise ValidationError(
            _('URL port is not a common HTTP port'),
        )
