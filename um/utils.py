from logging import getLogger

from django.utils import translation

logger = getLogger(__name__)


def set_session_language_if_necessary(request, user):
    preferred_language = user.um_profile.language
    if request.LANGUAGE_CODE == preferred_language:
        return

    if not translation.check_for_language(preferred_language):
        logger.warning('Invalid language %s for user %s',
                       preferred_language, user)
        return

    logger.info('Set language %s for user session %s', preferred_language, user)
    translation.activate(preferred_language)
    request.LANGUAGE_CODE = translation.get_language()
    request.session[translation.LANGUAGE_SESSION_KEY] = preferred_language
