from logging import getLogger
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from django.utils.timezone import now
from spinach import Tasks

from .settings import UM_DELETE_ACCOUNT_AFTER

tasks = Tasks()
logger = getLogger(__name__)


@tasks.task(name='um:delete_user')
def delete_user(user_id: int):
    try:
        user = get_user_model().objects.get(pk=user_id)
    except ObjectDoesNotExist:
        logger.info('Not deleting user with id %s: already deleted', user_id)
        return

    if not user.um_profile.deletion_pending:
        logger.info('Not deleting user %s: deletion not pending', user)
        return

    if user.last_login > now() - UM_DELETE_ACCOUNT_AFTER:
        logger.info('Not deleting user %s: last login %s',
                    user, user.last_login)
        return

    logger.info('Deleting user %s', user)
    user.delete()
