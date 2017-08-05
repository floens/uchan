# Dockerfile for our appserver ran by uwsgi

FROM alpine:3.6

# Some packages required for compiling some of the python libs, plus uwsgi.
RUN apk update &&\
    apk add python3-dev \
            uwsgi uwsgi-python3 \
            build-base \
            libffi-dev \
            libjpeg-turbo-dev \
            zlib-dev \
            postgresql-dev postgresql-client
ADD requirements /opt/app/requirements
WORKDIR /opt/app
RUN pip3 install -r requirements

RUN addgroup -S uchan && adduser -u 1001 -S uchan uchan

ADD . /opt/app
RUN mkdir -p /opt/app/data/log && chown -R uchan:uchan /opt/app/data/log && \
    mkdir -p /opt/app/data/media && chown -R uchan:uchan /opt/app/data/media && \
    mkdir -p /tmp/uchanmediaqueue && chown -R uchan:uchan /tmp/uchanmediaqueue

ENTRYPOINT ["./docker-entrypoint.sh"]
