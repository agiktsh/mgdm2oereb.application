FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y \
      git \
      python3-pip && \
    pip install reader requests

COPY . /app
