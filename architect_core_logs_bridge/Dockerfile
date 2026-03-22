ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3

WORKDIR /app

COPY run.sh /
COPY bridge.py /app/bridge.py

RUN chmod a+x /run.sh

CMD ["/run.sh"]
