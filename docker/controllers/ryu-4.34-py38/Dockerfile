FROM python:3.8-alpine

RUN apk update --no-cache

RUN apk upgrade --no-cache

RUN apk add --no-cache gcc g++ musl-dev

COPY docker/controllers/ryu-4.34-py38/requirements.txt /tmp/requirements.txt

RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

COPY docker/controllers/ryu-4.34-py38/controller-entrypoint.sh /usr/local/bin/controller-entrypoint

RUN chmod +x /usr/local/bin/controller-entrypoint

ENTRYPOINT ["controller-entrypoint"]