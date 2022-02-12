FROM python:3.9-slim as ws_proxy
ENV PYTHONUNBUFFERED=1
#RUN sed -Ei 's/main$/main contrib/' /etc/apt/sources.list
RUN apt-get update

COPY .configs/pip.conf /root/.pip/pip.conf
RUN pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

ENV REDIS_HOST='redis'

COPY ./app /app/app

WORKDIR /app

ENV PYTHONPATH=/app

EXPOSE 8000

FROM ws_proxy as ws_test

COPY requirements_test.txt /tmp/requirements_test.txt
RUN pip install -r /tmp/requirements_test.txt

COPY ./tests /app/tests
COPY pytest.ini /app/

WORKDIR /app/tests
