FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y \
      git \
      python3-pip && \
    pip install reader requests

ARG TINI_VERSION=v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

COPY . /app

ENTRYPOINT [ "/tini", "--", "/app/loop.sh" ]
