FROM geopython/pygeoapi:latest as dev

RUN apt-get update && \
    apt-get install -y \
      make \
      git

ARG MGDM2OEREB_VERSION=9b6634774f621b8d606e12f7aa56a2543cf36c34
RUN git clone https://github.com/openoereb/mgdm2oereb.git /mgdm2oereb && \
    cd /mgdm2oereb && \
    git checkout ${MGDM2OEREB_VERSION}

COPY ./ /app

WORKDIR /app

RUN make install build-dev

ENTRYPOINT make serve-dev
