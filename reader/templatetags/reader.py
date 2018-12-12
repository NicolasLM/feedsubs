import hashlib
import math
from typing import Optional
from urllib.parse import urlencode

from django import template

from .. import http_fetcher

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
def blur_subscriber_count(count: int) -> str:
    if count < 10:
        return '< 10'

    if count < 1000:
        return str(int(math.ceil(count / 10.0)) * 10)

    for unit in ('', 'K', 'M', 'G'):
        if abs(count) < 1000.0:
            return "%3.1f %s" % (count, unit)
        count /= 1000.0


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


@register.filter(name='dict_get')
def dict_get(d, k):
    """Returns the given key from a dictionary."""
    return d[k]
