"""Defines static boards that are common to every user.

Static boards act like users' boards except that they are shared by every users
and they don't only rely on feed tags to filter articles.
"""
from django.urls import reverse

from .models import Board


class StaticBoard:
    """Class that mimics the Board model interface."""
    is_static = True

    def __init__(self, pk, name, view_name):
        self.pk = pk
        self.name = name
        self.tags = list()
        self._view_name = view_name

    def get_absolute_url(self):
        return reverse('reader:' + self._view_name)


static_boards = {
    'all': StaticBoard('all', 'All articles', 'home'),
    'starred': StaticBoard('starred', 'Stars', 'starred')
}


def get_boards_for_user(user) -> list:
    """Retrieve all boards a user has access to: his and the static ones."""
    user_boards = Board.objects.filter(reader=user.reader_profile)
    return list(static_boards.values()) + list(user_boards)
