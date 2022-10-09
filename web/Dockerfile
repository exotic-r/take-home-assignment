FROM python:3.9.14-slim-buster

COPY . /

RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt && pip3 install gunicorn

ENV PYTHONPATH=/app

ENTRYPOINT ["/runserver.sh"]