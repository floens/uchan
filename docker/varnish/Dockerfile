# Dockerfile for varnish

FROM alpine:3.6

RUN apk update &&\
    apk add varnish

ADD uchan.vcl /etc/varnish/uchan.vcl

CMD ["sh", "-c", "varnishd -F -t 300 -s malloc,${UCHAN_VARNISH_MEMSIZE} -f /etc/varnish/uchan.vcl"]
