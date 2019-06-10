FROM python:3.7-stretch

ENTRYPOINT ["manage.py"]
ENV DJANGO_SETTINGS_MODULE=feedsubs.settings.prod

RUN mkdir /opt/code /opt/static

COPY requirements.txt /opt/code/
RUN pip install -U pip setuptools && pip install -r /opt/code/requirements.txt

COPY . /opt/code
RUN pip install /opt/code[prod]

# These secrets are only used to run collectstatic
RUN SECRET_KEY=x DB_PASSWORD=x EMAIL_HOST_PASSWORD=x SENTRY_DSN=https://9@xsfdf.rtd/2 AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x manage.py collectstatic

USER nobody

