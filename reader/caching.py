from django.core.cache import cache

from . import html_processing


def cache_id_to_key(article_id: int):
    return 'cleaned_article_{}'.format(article_id)


def cache_key_to_id(article_key: str):
    return int(article_key.split('cleaned_article_')[1])


def get_cleaned_articles(articles) -> dict:
    from_cache = cache.get_many([cache_id_to_key(a.id) for a in articles])
    rv = {cache_key_to_id(k): v for k, v in from_cache.items()}

    to_cache = dict()
    for article in articles:
        if article.id in rv:
            continue

        cleaned = html_processing.clean_article(
            article.content,
            base_url=article.feed.uri
        )
        rv[article.id] = cleaned
        to_cache[cache_id_to_key(article.id)] = cleaned

    if to_cache:
        cache.set_many(to_cache, timeout=7200)

    return rv


def remove_cleaned_articles(articles):
    cache.delete_many([cache_id_to_key(a.id) for a in articles])
