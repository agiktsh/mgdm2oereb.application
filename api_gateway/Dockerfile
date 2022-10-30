FROM caddy/caddy:2.6.2-alpine

COPY ./config/Caddyfile.json /etc/caddy/Caddyfile.json

ENTRYPOINT caddy run --config=/etc/caddy/Caddyfile.json

