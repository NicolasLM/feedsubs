from django.contrib.auth import logout
from django.contrib import messages

from .background_messages import get_messages


def user_management_middleware(get_response):
    """User Management Middleware.

    - Logs out user having an account pending deletion. All other sessions of
    the user should rather be cleared when the user requests the account
    deletion, but the way to do that is not obvious.
    - Fetches Messages sent by background tasks and gives them to
    django.contrib.message framework.
    """

    def middleware(request):
        if request.user.is_authenticated:
            if request.user.um_profile.deletion_pending:
                messages.info(
                    request,
                    'This account is about to be permanently deleted, sign in '
                    'again to reactivate it.'
                )
                logout(request)
            else:
                for msg, level in get_messages(request.user):
                    messages.add_message(request, level, msg)

        return get_response(request)

    return middleware
