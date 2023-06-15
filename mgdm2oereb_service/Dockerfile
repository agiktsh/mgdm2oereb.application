FROM geopython/pygeoapi:0.15.0 as dev

RUN apt-get update && \
    apt-get install -y \
      make \
      git

ARG MGDM2OEREB_VERSION=228f9fddda6f5eff6930422c24775f34d9028dc4
RUN git clone https://github.com/openoereb/mgdm2oereb.git /mgdm2oereb && \
    cd /mgdm2oereb && \
    git checkout ${MGDM2OEREB_VERSION}

COPY ./ /app

WORKDIR /app

RUN make install build-dev

ENTRYPOINT make serve-dev
