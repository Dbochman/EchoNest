# Hello friend!
#
# Build and run:
#  $ docker build -t andre .
#  $ docker run -p 5000:5000 --env-file .env andre
#
# This container expects Redis to be reachable at REDIS_HOST/REDIS_PORT.
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libevent-dev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /prosecco
COPY . /prosecco

RUN pip install --no-cache-dir pip==23.3.2 setuptools==57.5.0 \
    && pip install --no-cache-dir -r /prosecco/requirements.txt

ADD supervise/player.conf /etc/supervisor/conf.d/player.conf
ADD supervise/main.conf /etc/supervisor/conf.d/main.conf

EXPOSE 5000

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
