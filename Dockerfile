FROM python:3.6-stretch

ENTRYPOINT ["manage.py"]
ENV DJANGO_SETTINGS_MODULE=feedsubs.settings.prod

RUN mkdir /opt/code /opt/static

RUN apt-get update && \
    apt-get install -y --no-install-recommends libmemcached-dev && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt /opt/code/
RUN pip install -U pip setuptools && pip install -r /opt/code/requirements.txt

COPY . /opt/code
RUN pip install /opt/code[prod]

# These secrets are only used to run collectstatic, there is no problem
# in making them public
RUN SECRET_KEY=snakeoil DB_PASSWORD=snakeoil EMAIL_HOST_PASSWORD=snakeoil SENTRY_DSN=foo manage.py collectstatic

USER nobody

