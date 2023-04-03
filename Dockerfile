FROM python:3.9-slim as ws_proxy
ENV PYTHONUNBUFFERED=1
#RUN sed -Ei 's/main$/main contrib/' /etc/apt/sources.list
RUN apt-get update

COPY .configs/pip.conf /root/.pip/pip.conf
RUN pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt


COPY ./app /app/app

WORKDIR /app

EXPOSE 8000

ENTRYPOINT ["python", "app/main.py"]
