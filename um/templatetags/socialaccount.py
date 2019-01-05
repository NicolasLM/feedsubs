"""Hack to use account/login.html without having socialaccount app installed."""
from django import template

register = template.Library()


@register.simple_tag()
def get_providers():
    pass
