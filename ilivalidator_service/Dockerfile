FROM sogis/ilivalidator-web-service@sha256:fe819acddf98ed9c2389549b6033eb1b1e691b7f51a7bd013d115da055ea83fc
LABEL authors="Clemens Rudert"

USER 0

ARG TINI_VERSION=v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini && chown $UID:0 /tini

ADD entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh && chown $UID:0 /usr/local/bin/entrypoint.sh

USER $UID

ENTRYPOINT [ "/tini", "--", "/usr/local/bin/entrypoint.sh" ]
