from datetime import datetime
import hashlib
from logging import getLogger
from typing import Optional

import attr
from django.utils.http import http_date
from django.contrib.sites.models import Site
import requests

logger = getLogger(__name__)


@attr.s
class FeedFetchResult:
    content: bytes = attr.ib()
    hash: bytes = attr.ib()
    is_html: bool = attr.ib()
    final_url: str = attr.ib()


def fetch_feed(uri: str, last_fetched_at: Optional[datetime],
               last_hash: Optional[bytes], subscriber_count: int,
               feed_id: Optional[int]) -> Optional[FeedFetchResult]:
    """Retrieve a new version of the feed via HTTP if available."""
    request_headers = {
        'User-Agent': get_user_agent(subscriber_count, feed_id)
    }
    if last_fetched_at:
        request_headers['If-Modified-Since'] = http_date(
            last_fetched_at.timestamp()
        )
    r = requests.get(uri, headers=request_headers, timeout=(15, 120))
    r.raise_for_status()

    if r.status_code == 304:
        logger.info('Feed did not change since last fetch, got HTTP 304')
        return None

    current_hash = hashlib.sha1(r.content).digest()
    if last_hash == current_hash:
        logger.info('Feed did not change since last fetch, hashes match')
        return None

    is_html = r.headers.get('Content-Type', '').startswith('text/html')

    return FeedFetchResult(r.content, current_hash, is_html, r.url)


def fetch_image(session: requests.Session, uri: str) -> bytes:
    """Retrieve an image."""
    request_headers = {
        'User-Agent': get_user_agent(0)
    }
    r = session.get(uri, headers=request_headers, timeout=(15, 120))
    r.raise_for_status()
    return r.content


def get_user_agent(subscriber_count: int,
                   feed_id: Optional[int]=None) -> str:
    """Generate a user-agent allowing publisher to gather subscribers count.

    See https://support.feed.press/article/66-how-to-be-a-good-feed-fetcher
    """
    service_name = Site.objects.get_current().domain
    help_page = 'https://github.com/NicolasLM/feedsubs'
    feed_id = '' if feed_id is None else '; feed-id={}'.format(feed_id)
    return '{}; (+{}; {} subscribers{})'.format(
        service_name, help_page, subscriber_count, feed_id
    )
