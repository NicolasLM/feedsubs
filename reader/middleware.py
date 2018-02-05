from django.contrib.auth import logout
from django.contrib import messages


def logout_deletion_pending(get_response):
    """Middleware that logs out user having a account pending deletion."""

    def middleware(request):
        if (request.user.is_authenticated and
                request.user.profile.deletion_pending):
            messages.info(
                request,
                'This account is about to be permanently deleted, sign in '
                'again to reactivate it.'
            )
            logout(request)

        return get_response(request)

    return middleware
