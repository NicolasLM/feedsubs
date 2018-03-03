from logging import getLogger
import time

logger = getLogger('waitress.access')


def access_log(get_response):

    def middleware(request):
        start_time = time.monotonic()
        response = get_response(request)
        duration_ms = int((time.monotonic() - start_time) * 1000)
        try:
            user = request.user
        except AttributeError:
            user = 'No user'

        logger.info(
            '%d %s %s (%s %s) %d ms', response.status_code,
            request.method, request.get_full_path(),
            request.META['REMOTE_ADDR'], user, duration_ms
        )

        return response

    return middleware
