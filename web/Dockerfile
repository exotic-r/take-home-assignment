FROM python:3.9.14-slim-buster

COPY . /
ENV PYTHONPATH=/app


RUN apt-get update && \
    apt-get -y install gcc mono-mcs && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt && pip3 install gunicorn

ENTRYPOINT ["gunicorn", "--log-level", "info", "--workers", "4", "-b", "0.0.0.0:8000", "app:app"]