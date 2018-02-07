FROM python:3.6-stretch

ENTRYPOINT ["manage.py"]

RUN mkdir /opt/code /opt/static

COPY requirements.txt /opt/code/
RUN pip install -U pip setuptools && pip install -r /opt/code/requirements.txt

COPY . /opt/code
RUN pip install /opt/code
RUN manage.py collectstatic

USER nobody

