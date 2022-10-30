FROM geopython/pygeoapi:latest as dev

RUN apt-get update && \
    apt-get install -y \
      make \
      git

ARG MGDM2OEREB_VERSION=a28aefbae33b9241ad2ecf175c710146d202cd33
RUN git clone https://github.com/openoereb/mgdm2oereb.git /mgdm2oereb && \
    cd /mgdm2oereb && \
    git checkout ${MGDM2OEREB_VERSION}

COPY ./ /app

WORKDIR /app

RUN make install build-dev

ENTRYPOINT make serve-dev
