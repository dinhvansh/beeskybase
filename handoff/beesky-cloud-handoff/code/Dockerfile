# BeeSky web dashboard — stdlib-only, so the slim base image is all we need.
FROM python:3.12-slim

WORKDIR /app
COPY beesky/ ./beesky/

# The dashboard only ever scans the network this container can reach —
# see docs/web.md for the farm-LAN caveat before deploying anywhere.
ENV BEESKY_TARGET=192.168.1.0/24 \
    BEESKY_INTERVAL=30

EXPOSE 8787 8788

# sh -c is used on purpose so ${BEESKY_TARGET} / ${BEESKY_INTERVAL} expand
# at container start (they are runtime config, not build-time values).
CMD ["sh", "-c", "exec python -m beesky serve \"$BEESKY_TARGET\" --host 0.0.0.0 --port 8787 --interval \"$BEESKY_INTERVAL\""]
