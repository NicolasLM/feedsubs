import hashlib
from typing import Optional

import bleach
import bs4
from django import template

ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['p', 'pre', 'img', 'br', 'h1', 'h2',
                                      'h3', 'h4', 'h5', 'h6']
ALLOWED_ATTRIBUTES = {'img': ['src', 'title', 'alt']}
ALLOWED_ATTRIBUTES.update(bleach.ALLOWED_ATTRIBUTES)
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
def clean_article(content: str) -> str:
    """Clean and format an untrusted chunck of HTML.

    This filter cleans the HTML from dangerous tags and formats it so that
    it fits with the style of the surrounding document by shifting titles.
    """
    content = bleach.clean(
        content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )
    return unify_style(content)


def unify_style(content: str) -> str:
    # The surrounding page uses h1 and h2, user content must start at h3
    shift_by = 2
    soup = bs4.BeautifulSoup(content, 'html.parser')

    highest_title = 1
    for i in range(10, 0, -1):
        title_tag_name = 'h{}'.format(i)
        if soup.find(title_tag_name):
            highest_title = i

    shift_by = shift_by - highest_title + 1
    for i in range(10, 0, -1):
        title_tag_name = 'h{}'.format(i)
        for tag in soup.find_all(title_tag_name):
            tag.name = 'h{}'.format(i + shift_by)

    return soup.prettify()


@register.filter
def tag_color(tag_name: str) -> str:
    colors = [
        'dark', 'primary', 'link', 'info', 'success', 'warning', 'danger',
        'black', 'white'
    ]
    index = int(hashlib.md5(tag_name.encode()).hexdigest(), 16) % (len(colors))
    return colors[index]
