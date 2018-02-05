from typing import Optional

from django import template

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
