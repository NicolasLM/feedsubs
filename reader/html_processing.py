from typing import Optional
import urllib.parse

import bleach
import bs4

ALLOWED_TAGS = bleach.ALLOWED_TAGS + ['p', 'pre', 'img', 'br', 'h1', 'h2',
                                      'h3', 'h4', 'h5', 'h6']
ALLOWED_ATTRIBUTES = {'img': ['src', 'title', 'alt']}
ALLOWED_ATTRIBUTES.update(bleach.ALLOWED_ATTRIBUTES)
URL_REWRITE_PAIRS = (
    ('a', 'href'),
    ('img', 'src')
)


def clean_article(content: str, base_url: str=None) -> str:
    """Clean and format an untrusted chunk of HTML.

    This filter cleans the HTML from dangerous tags and formats it so that
    it fits with the style of the surrounding document by shifting titles.
    """
    soup = bs4.BeautifulSoup(content, 'html.parser')
    remove_unwanted_tags(soup)
    unify_style(soup)
    rewrite_relative_links(soup, base_url)
    content = soup.prettify()

    content = bleach.clean(
        content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
    )

    return content


def remove_unwanted_tags(soup: bs4.BeautifulSoup):
    """Remove unwanted tags from the HTML tree.

    Bleach cannot be used to remove completely scripts and style tags because
    bleach cannot remove the content inside these tags, leaving javascript code
    or css as plain text.
    """
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()


def rewrite_relative_links(soup: bs4.BeautifulSoup, base_url: str):
    """Rewrite relative links in feeds to absolute ones.

    Feeds should only contain absolute references to other resources. For feeds
    using relative references, the best guess is to use the URL of the feed
    as base resource.
    """
    for tag_name, attrib in URL_REWRITE_PAIRS:
        for tag in soup.find_all(tag_name, attrs={attrib: True}):
            tag[attrib] = urllib.parse.urljoin(base_url, tag[attrib])


def unify_style(soup: bs4.BeautifulSoup):
    """Unify hierarchy of titles in an HTML page.

    Feeds often embed HTML using titles in an incorrect way, this function tries
    to reorganize them so that the resulting page has a proper title hierarchy.
    The surrounding page uses h1 and h2 so user content must start at h3.
    """
    shift_by = 2

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


def find_feed_in_html(html_content: bytes, from_url: str) -> Optional[str]:
    """Find linked feed URL in HTML page header."""
    soup = bs4.BeautifulSoup(html_content, 'html.parser')
    for type_ in ('application/atom+xml', 'application/rss+xml'):
        link = soup.find('link', type=type_)
        if not link:
            continue

        link = link.get('href')
        if not link:
            continue

        return urllib.parse.urljoin(from_url, link)
