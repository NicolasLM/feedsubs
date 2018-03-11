FROM python:3.6-stretch

ENTRYPOINT ["manage.py"]
ENV DJANGO_SETTINGS_MODULE=feedsubs.settings.prod

RUN mkdir /opt/code /opt/static

COPY requirements.txt /opt/code/
RUN pip install -U pip setuptools && pip install -r /opt/code/requirements.txt

COPY . /opt/code
RUN pip install /opt/code[prod]

USER nobody

