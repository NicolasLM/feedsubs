Feedsubs
========

.. image:: https://travis-ci.org/NicolasLM/feedsubs.svg?branch=master
    :target: https://travis-ci.org/NicolasLM/feedsubs
.. image:: https://coveralls.io/repos/github/NicolasLM/feedsubs/badge.svg?branch=master
    :target: https://coveralls.io/github/NicolasLM/feedsubs?branch=master

RSS feed reader for Python 3.

.. image:: https://raw.githubusercontent.com/NicolasLM/feedsubs/master/misc/screenshot.png
    :target: https://feedsubs.com

Features:

* Support for RSS, Atom and JSON feeds
* Background synchronization
* Caching and resizing of image embedded in feeds
* Removal of tracking pixels
* Grouping of feeds with tags
* Multi-users
* MIT licensed

Hosted service
--------------

A free hosted version runs Feedsubs at `feedsubs.com <https://feedsubs.com>`_,
it is the easiest way to start using the software without installing anything.

Development guide
-----------------

Feedsubs is a typical Django project, anyone familiar with Django will feel
right at home. It requires:

* Python 3.6+
* Postgresql database
* Redis server for background tasks

Quickstart::

    git clone git@github.com:NicolasLM/feedsubs.git
    cd feedsubs/
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .[dev]
    touch .env  # Put SECRET_KEY=foo and DB_PASSWORD=foo there
    manage.py migrate
    manage.py runserver

Background task workers can be started with::

    manage.py spinach


Self-hosting
------------

Feedsubs is a feed reader primarily focused toward large multi-users
installations, it may not be the easiest choice to host as a personal reader.
That being said, Docker makes it simple to deploy:

* Make your own settings module based on `feedsubs/settings/prod.py`
* ``docker run -d -v path/to/my_settings.py:/my_settings.py -e DJANGO_SETTINGS_MODULE=my_settings -p 8000:8000 nicolaslm/feedsubs waitress``
* Serve the port 8000 through a reverse proxy like nginx or caddy

Users can also deploy Feedsubs with pip instead of Docker::

   pip install feedsubs[prod]
   manage.py waitress

