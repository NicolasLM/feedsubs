from datetime import timedelta

from django.conf import settings


UM_DELETE_ACCOUNT_AFTER = getattr(settings, 'UM_DELETE_ACCOUNT_AFTER',
                                  timedelta(days=2))
