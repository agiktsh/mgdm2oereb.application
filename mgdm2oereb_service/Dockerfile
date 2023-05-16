FROM geopython/pygeoapi:latest as dev

RUN apt-get update && \
    apt-get install -y \
      make \
      git

ARG MGDM2OEREB_VERSION=c7ea8faeade470fb51c2b4172c0a4afad14b021b
RUN git clone https://github.com/openoereb/mgdm2oereb.git /mgdm2oereb && \
    cd /mgdm2oereb && \
    git checkout ${MGDM2OEREB_VERSION}

COPY ./ /app

WORKDIR /app

RUN make install build-dev

ENTRYPOINT make serve-dev
