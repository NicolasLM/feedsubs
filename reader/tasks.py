from datetime import datetime, timedelta
import hashlib
from logging import getLogger
from typing import Optional, Tuple

from atoma.simple import simple_parse_bytes
from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.utils.http import http_date
import requests
from spinach import Tasks, Batch

from . import models


tasks = Tasks()
logger = getLogger(__name__)


@tasks.task(name='synchronize_all_feeds', periodicity=timedelta(minutes=30))
def synchronize_all_feeds():
    batch = Batch()
    for feed in models.Feed.objects.all():
        batch.schedule('synchronize_feed', feed.id)
    tasks.schedule_batch(batch)


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
    parsed_feed = simple_parse_bytes(feed_content)
    for parsed_article in reversed(parsed_feed.articles):

        article, created = models.Article.objects.update_or_create(
            id_in_feed=parsed_article.id,
            feed=feed,
            defaults={
                'uri': parsed_article.link,
                'title': parsed_article.title,
                'content': parsed_article.content,
                'published_at': parsed_article.published_at,
                'updated_at': parsed_article.updated_at
            }
        )
        if created:
            logger.info('Created article %s', parsed_article.id)
        else:
            logger.info('Updated article %s', parsed_article.id)

    if feed.name != parsed_feed.title:
        logger.info('Renaming feed %d from "%s" to "%s"', feed_id, feed.name,
                    parsed_feed.title)
        feed.name = parsed_feed.title

    feed.last_fetched_at = task_start_date
    feed.last_hash = current_hash
    feed.frequency_per_year = calculate_frequency_per_year(feed)
    feed.save()


@tasks.task(name='create_feed')
def create_feed(user_id: int, uri: str):
    try:
        user = get_user_model().objects.get(pk=user_id)
    except ObjectDoesNotExist:
        logger.warning('Not creating feed "%s" as user %d does not exist',
                       uri, user_id)
        return

    # Check if the feed already exists
    try:
        feed = models.Feed.objects.get(uri=uri)
    except ObjectDoesNotExist:
        creation_needed = True
    else:
        creation_needed = False
        logger.info('Feed already exists: %s', feed)

    if creation_needed:
        feed_content, _ = retrieve_feed(uri, None, None)
        parsed_feed = simple_parse_bytes(feed_content)
        feed = models.Feed.objects.create(
            name=parsed_feed.title[:100],
            uri=uri,
        )
        logger.info('Created feed %s', feed)

    subscription = models.Subscription(
        feed=feed, reader=user.reader_profile
    )
    try:
        subscription.save()
    except IntegrityError as e:
        logger.warning('User probably already subscribed to the feed: %s', e)
    else:
        logger.info('User subscribed to feed')


def calculate_frequency_per_year(feed: models.Feed) -> Optional[int]:
    last_year = now() - timedelta(days=365)
    num_articles_over_year = (
        feed.article_set.filter(published_at__gt=last_year).count()
    )
    oldest_article = (
        feed.article_set.filter(published_at__gt=last_year)
        .order_by('published_at').first()
    )
    if oldest_article is None:
        return None

    try:
        yearly_ratio = 365 / (now() - oldest_article.published_at).days
    except ZeroDivisionError:
        # Oldest article has been published today
        return None

    return int(num_articles_over_year * yearly_ratio)


def retrieve_feed(uri: str, last_fetched_at: Optional[datetime],
                  last_hash: Optional[bytes]) -> Optional[Tuple[bytes, bytes]]:
    """Retrieve a new version of the feed via HTTP if available."""
    request_headers = dict()
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

    return r.content, current_hash
