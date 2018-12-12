# Adapted from django-async-messages under the MIT license:
#
# Copyright (C) 2012 django-async-messages authors (see AUTHORS file)
#
# Permission is hereby granted, free of charge to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from django.core.cache import cache
from django.contrib.messages import constants, add_message


def message_user(user, message, level=constants.INFO):
    """Send a message to a particular user.

    A list of messages is stored in the cache to allow having multiple messages
    queued up for a user. This non-atomic read-modify-write makes it possible
    to lose messages under concurrency.

    :param user: User instance
    :param message: Message to show
    :param level: Message level
    """
    if user.id is None:
        raise ValueError('Anonymous users cannot send messages')

    user_key = _user_key(user)
    messages = cache.get(user_key) or []
    messages.append((message, level))
    cache.set(user_key, messages)


def _get_messages(user):
    """Fetch messages for given user.

    :param user: User instance
    """
    if user.id is None:
        return []

    key = _user_key(user)
    result = cache.get(key)
    if result:
        cache.delete(key)
        return result

    return []


def add_background_messages_to_contrib_messages(request):
    """Merge background messages with normal contrib.message."""
    for msg, level in _get_messages(request.user):
        add_message(request, level, msg)


def _user_key(user):
    if isinstance(user, int):
        return '_async_message_%d' % user
    else:
        return '_async_message_%d' % user.pk


def debug(user, message):
    """
    Adds a message with the ``DEBUG`` level.

    :param user: User instance
    :param message: Message to show
    """
    message_user(user, message, constants.DEBUG)


def info(user, message):
    """
    Adds a message with the ``INFO`` level.

    :param user: User instance
    :param message: Message to show
    """
    message_user(user, message, constants.INFO)


def success(user, message):
    """
    Adds a message with the ``SUCCESS`` level.

    :param user: User instance
    :param message: Message to show
    """
    message_user(user, message, constants.SUCCESS)


def warning(user, message):
    """
    Adds a message with the ``WARNING`` level.

    :param user: User instance
    :param message: Message to show
    """
    message_user(user, message, constants.WARNING)


def error(user, message):
    """
    Adds a message with the ``ERROR`` level.

    :param user: User instance
    :param message: Message to show
    """
    message_user(user, message, constants.ERROR)
