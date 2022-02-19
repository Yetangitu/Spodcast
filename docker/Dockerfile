FROM python:3-alpine

COPY . /app
WORKDIR /app

RUN apk --no-cache add gcc libc-dev \
	&& pip3 install .

VOLUME ["/data"]
WORKDIR /data

ENTRYPOINT ["/usr/local/bin/spodcast"]
