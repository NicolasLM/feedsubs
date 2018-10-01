from datetime import timedelta
from logging import getLogger
import random
from typing import Optional

from atoma.exceptions import FeedDocumentError
from atoma.simple import simple_parse_bytes
from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.db.models import Count, Q, ObjectDoesNotExist
from django.db.utils import IntegrityError
from django.template.defaultfilters import filesizeformat
from django.utils.timezone import now
from psycopg2 import errorcodes as pg_error_codes
import requests
from spinach import Tasks, Batch

from um import background_messages

from . import models, html_processing, image_processing, http_fetcher


tasks = Tasks()
logger = getLogger(__name__)


@tasks.task(name='synchronize_all_feeds', periodicity=timedelta(minutes=30))
def synchronize_all_feeds():
    """Synchronize all feeds every 30 minutes.

    To avoid a spike of load, the synchronization is spread over a 20 minutes
    period.
    """
    current_date = now()
    ats = list()
    for i in range(0, 20):
        ats.append(current_date + timedelta(minutes=i))

    batch = Batch()
    for feed_id in models.Feed.objects.values_list('id', flat=True):
        batch.schedule_at('synchronize_feed', random.choice(ats), feed_id)
    tasks.schedule_batch(batch)


@tasks.task(name='synchronize_feed')
def synchronize_feed(feed_id: int):
    task_start_date = now()

    # Fetch the feed from db as well as its subscribers count in a single query,
    # this approach may give incorrect results if other annotations are added
    # in the future. See https://code.djangoproject.com/ticket/10060
    feed = models.Feed.objects.annotate(Count('subscribers')).get(pk=feed_id)

    try:
        feed_request = http_fetcher.fetch_feed(
            feed.uri,
            feed.last_fetched_at,
            bytes(feed.last_hash) if feed.last_hash else None,
            feed.subscribers__count,
            feed_id
        )
    except (requests.exceptions.RequestException,
            http_fetcher.FetchFileTooBigError) as e:
        logger.warning('Could not synchronize %s: %s', feed, e)
        feed.last_failure = repr(e)
        feed.save()
        return

    if feed_request is None:
        feed.last_fetched_at = task_start_date
        feed.last_failure = ''
        feed.save()
        return

    if feed_request.is_html:
        logger.warning('Fetch of %s gave an HTML page', feed)

    try:
        parsed_feed = simple_parse_bytes(feed_request.content)
    except FeedDocumentError as e:
        logger.warning('Could not synchronize %s: %s', feed, e)
        feed.last_failure = repr(e)
        feed.save()
        return

    images_uris = set()
    for parsed_article in reversed(parsed_feed.articles):
        article, created = models.Article.objects.update_or_create(
            id_in_feed=parsed_article.id,
            feed=feed,
            defaults={
                'uri': parsed_article.link,
                'title': parsed_article.title or '',
                'content': parsed_article.content,
                'published_at': parsed_article.published_at,
                'updated_at': parsed_article.updated_at
            }
        )
        if created:
            logger.info('Created article %s', parsed_article.id)
        else:
            logger.info('Updated article %s', parsed_article.id)
        images_uris.update(
            html_processing.find_images_in_article(parsed_article.content,
                                                   feed.uri)
        )

        current_attachments_ids = list()
        for parsed_attachment in parsed_article.attachments:
            attachment, created = models.Attachment.objects.update_or_create(
                uri=parsed_attachment.link,
                article=article,
                defaults={
                    'title': parsed_attachment.title,
                    'mime_type': parsed_attachment.mime_type or '',
                    'size_in_bytes': parsed_attachment.size_in_bytes or None,
                    'duration': parsed_attachment.duration
                }
            )
            current_attachments_ids.append(attachment.id)
            if created:
                logger.info('Created attachment %s', attachment)
            else:
                logger.info('Updated attachment %s', attachment)

        deleted_attachments, _ = (
            models.Attachment.objects
            .filter(article=article)
            .filter(~Q(id__in=current_attachments_ids))
            .delete()
        )
        if deleted_attachments:
            logger.info('Deleted %d old attachments', deleted_attachments)

    if feed.name != parsed_feed.title:
        logger.info('Renaming feed %d from "%s" to "%s"', feed_id, feed.name,
                    parsed_feed.title)
        feed.name = parsed_feed.title

    feed.last_fetched_at = task_start_date
    feed.last_hash = feed_request.hash
    feed.last_failure = ''
    feed.frequency_per_year = calculate_frequency_per_year(feed)
    feed.save()

    number_of_images = len(images_uris)
    if number_of_images > 1000:
        logger.error('Too many images to cache: %d', number_of_images)
        return
    cache_images(images_uris)


@tasks.task(name='cache_images')
def cache_images(images_uris):
    already_cached_uris = (
        models.CachedImage.objects
        .filter(uri__in=images_uris)
        .values_list('uri', flat=True)
    )
    already_cached_uris = set(already_cached_uris)
    images_uris = [u for u in images_uris if u not in already_cached_uris]
    logger.info('Attempting to cache %d images (%d already cached)',
                len(images_uris), len(already_cached_uris))

    with requests.Session() as session:
        for image_uri in images_uris:
            try:
                image_data = http_fetcher.fetch_image(session, image_uri)
                processed = image_processing.process_image_data(image_data)
            except (requests.RequestException,
                    http_fetcher.FetchFileTooBigError,
                    image_processing.ImageProcessingError) as e:
                failure_reason = str(e)
                logger.warning('Failed to cache image: %s', failure_reason)
                _create_cached_image_object(
                    uri=image_uri,
                    failure_reason=failure_reason[:99]
                )
                continue

            cached_image = _create_cached_image_object(
                uri=image_uri,
                format=processed.image_format,
                width=processed.width,
                height=processed.height,
                size_in_bytes=processed.size_in_bytes
            )
            if cached_image is None:
                continue

            try:
                default_storage.save(
                    cached_image.image_path, File(processed.data)
                )
            except Exception:
                cached_image.delete()
                raise

            logger.info('Cached image %s %dx%d %s', cached_image.format,
                        cached_image.width, cached_image.height,
                        filesizeformat(cached_image.size_in_bytes))


def _create_cached_image_object(**kwargs) -> Optional[models.CachedImage]:
    """Save a CachedImage to database or fail silently if it already exists."""
    try:
        return models.CachedImage.objects.create(**kwargs)
    except IntegrityError as e:
        if e.__cause__.pgcode == pg_error_codes.UNIQUE_VIOLATION:
            logger.info('Cached image already exists in database')
            return None

        raise


@tasks.task(name='create_feed')
def create_feed(user_id: int, uri: str, process_html=True):
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
        try:
            feed_request = http_fetcher.fetch_feed(uri, None, None, 1, None)
        except (requests.exceptions.RequestException,
                http_fetcher.FetchFileTooBigError) as e:
            msg = f'Could not create feed "{uri}", HTTP fetch failed'
            logger.warning('%s: %s', msg, e)
            background_messages.warning(user, msg)
            return

        if feed_request.is_html and not process_html:
            # An HTML page gave a feed link that is another HTML page
            msg = f'Could find valid feed in HTML page "{uri}"'
            logger.warning(msg)
            background_messages.warning(user, msg)
            return

        if feed_request.is_html and process_html:
            found_uri = html_processing.find_feed_in_html(
                feed_request.content, feed_request.final_url
            )
            if not found_uri:
                # An HTML page does not contain a feed link
                msg = f'Could find valid feed in HTML page "{uri}"'
                logger.warning(msg)
                background_messages.warning(user, msg)
                return

            return create_feed(user_id, found_uri, process_html=False)

        try:
            parsed_feed = simple_parse_bytes(feed_request.content)
        except FeedDocumentError:
            msg = f'Could not create feed "{uri}", content is not a valid feed'
            logger.warning(msg)
            background_messages.warning(user, msg)
            return

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
