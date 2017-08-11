# Dockerfile for our appserver ran by uwsgi

FROM alpine:3.6

# Some packages required for compiling some of the python libs, plus uwsgi.
RUN apk update &&\
    apk add python3-dev \
            uwsgi uwsgi-python3 \
            build-base bash \
            libffi-dev \
            libjpeg-turbo-dev \
            zlib-dev \
            postgresql-dev postgresql-client \
            nodejs nodejs-npm

ADD requirements /opt/app/requirements
WORKDIR /opt/app
RUN pip3 install -r requirements

RUN npm install --no-progress -qpg clean-css@3 typescript

RUN addgroup -S uchan && adduser -u 1001 -S uchan uchan && \
    mkdir -p /tmp/uchanmediaqueue && chown -R uchan:uchan /tmp/uchanmediaqueue

ADD . /opt/app

ENTRYPOINT ["./docker-entrypoint.sh"]
