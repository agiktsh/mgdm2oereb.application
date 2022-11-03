FROM python:3.8-alpine3.16 as dev

RUN apk update && apk add \
        build-base \
        unzip \
        git \
        python3-dev \
        py3-pip \
        py3-setuptools \
        py3-wheel \
        zlib-dev \
        libjpeg-turbo-dev \
        libxml2-dev \
        libxslt-dev \
        freetype-dev

ENV DEVELOPMENT=true \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US \
    LC_ALL=en_US.UTF-8

COPY ./ /app

WORKDIR /app

RUN pip3 install -r requirements.txt -r requirements-tests.txt

RUN make install build build-dev

ENTRYPOINT make serve-dev
