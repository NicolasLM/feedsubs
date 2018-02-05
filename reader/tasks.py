from datetime import datetime
import hashlib
from logging import getLogger
from typing import Optional, Tuple

import atoma
import bs4
from django.utils.timezone import now
from django.utils.http import http_date
import bleach
import requests
from spinach import Tasks

from . import models

ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['p', 'pre', 'img', 'h1', 'h2',
                                      'h3', 'h4', 'h5', 'h6']
ALLOWED_ATTRIBUTES = {'img': ['src', 'title', 'alt']}
ALLOWED_ATTRIBUTES.update(bleach.ALLOWED_ATTRIBUTES)

tasks = Tasks()
logger = getLogger(__name__)


@tasks.task(name='synchronize_feed')
def synchronize_feed(feed_id: int):
    task_start_date = now()
    feed = models.Feed.objects.get(pk=feed_id)

    feed_request = retrieve_feed(
        feed.uri, feed.last_fetched_at,
        bytes(feed.last_hash) if feed.last_hash else None
    )
    if feed_request is None:
        feed.last_fetched_at = task_start_date
        feed.save()
        return

    feed_content, current_hash = feed_request
    parsed_feed = atoma.parse_atom_bytes(feed_content)
    for entry in parsed_feed.entries:
        content = entry.content or entry.summary
        content = content.value if content else ''
        content = bleach.clean(content, tags=ALLOWED_TAGS,
                               attributes=ALLOWED_ATTRIBUTES, strip=True)
        content = unify_style(content)

        published_at, updated_at = get_article_dates(entry)

        article, created = models.Article.objects.update_or_create(
            id_in_feed=entry.id_, feed=feed,
            defaults={
                'uri': entry.links[0].href,
                'title': entry.title.value,
                'content': content,
                'published_at': published_at,
                'updated_at': updated_at
            }
        )
        if created:
            logger.info('Created article %s', entry.id_)
        else:
            logger.info('Updated article %s', entry.id_)

    feed.last_fetched_at = task_start_date
    feed.last_hash = current_hash
    feed.save()


def retrieve_feed(uri: str, last_fetched_at: Optional[datetime],
                  last_hash: Optional[bytes]) -> Optional[Tuple[bytes, bytes]]:
    """Retrieve a new version of the feed via HTTP if available."""
    request_headers = dict()
    if last_fetched_at:
        request_headers['If-Modified-Since'] = http_date(
            last_fetched_at.timestamp()
        )
    r = requests.get(uri, headers=request_headers)
    r.raise_for_status()

    if r.status_code == 304:
        logger.info('Feed did not change since last fetch, got HTTP 304')
        return None

    current_hash = hashlib.sha1(r.content).digest()
    if last_hash == current_hash:
        logger.info('Feed did not change since last fetch, hashes match')
        return None

    return r.content, current_hash


def get_article_dates(entry: atoma.AtomEntry
                      ) -> Tuple[Optional[datetime], Optional[datetime]]:
    if entry.published and entry.updated:
        return entry.published, entry.updated

    if entry.updated:
        return entry.updated, None

    if entry.published:
        return entry.published, None

    raise ValueError('Entry does not have proper dates')


def unify_style(content: str) -> str:
    soup = bs4.BeautifulSoup(content, 'html.parser')
    shift_title(soup, 2)
    return soup.prettify()


def shift_title(soup: bs4.BeautifulSoup, shift_by: int):
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
