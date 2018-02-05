import logging.config

from django.conf import settings
import waitress

from feedpubsub.wsgi import application as app

logging.config.dictConfig(settings.LOGGING)
waitress.serve(app=app, port=8000)
