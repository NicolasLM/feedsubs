import hashlib
from typing import Optional
from urllib.parse import urlencode

from django import template

from .. import html_processing, http_fetcher

register = template.Library()


@register.filter
def humanize_yearly_frequency(value: Optional[int]) -> str:
    if value is None:
        return 'Unknown'

    if value <= 1:
        return '1/year'

    if value <= 12:
        return f'{value}/year'

    if value <= 52:
        return '{}/month'.format(int(value / 12))

    if value <= 365:
        return '{}/week'.format(int(value / 52))

    return '{}/day'.format(int(value / 365))


@register.filter
def clean_article(content: str, base_url: str=None) -> str:
    """Clean and format an untrusted chunk of HTML.

    This filter cleans the HTML from dangerous tags and formats it so that
    it fits with the style of the surrounding document by shifting titles.
    """
    return html_processing.clean_article(content, base_url=base_url)


@register.filter
def tag_color(tag_name: str) -> str:
    colors = [
        'dark', 'primary', 'link', 'info', 'success', 'warning', 'danger',
        'black', 'white'
    ]
    index = int(hashlib.md5(tag_name.encode()).hexdigest(), 16) % (len(colors))
    return colors[index]


@register.filter
def content_type_to_icon(content_type: str) -> str:
    if content_type == 'audio':
        return 'fa-headphones'
    elif content_type == 'image':
        return 'fa-image'
    elif content_type == 'text':
        return 'fa-file-alt'
    elif content_type == 'video':
        return 'fa-film'
    else:
        return 'fa-file'


@register.filter
def example_user_agent(_) -> str:
    return http_fetcher.get_user_agent(subscriber_count=42, feed_id=2940953)


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.dict()
    query.update(kwargs)
    return urlencode(query)
