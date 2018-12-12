from django import template

from ..background_messages import add_background_messages_to_contrib_messages

register = template.Library()


@register.simple_tag(takes_context=True)
def fetch_background_messages(context):
    """Template tag adding background messages to contrib message framework."""
    add_background_messages_to_contrib_messages(context['request'])
    return ''
