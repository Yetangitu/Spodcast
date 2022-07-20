FROM python:3-alpine

COPY . /app
WORKDIR /app

RUN apk --no-cache add gcc libc-dev ffmpeg \
	&& pip3 install .

VOLUME ["/data"]
WORKDIR /data

ENTRYPOINT ["/usr/local/bin/spodcast"]

LABEL description="Spodcast is a caching Spotify podcast to RSS proxy. \
Using Spodcast you can follow Spotify-hosted netcasts/podcasts using any \
player which supports RSS, thus enabling the use of older hardware which \
is not compatible with the Spotify (web) app."
LABEL version="0.5.2"
LABEL org.opencontainers.image.authors="Yetangitu and others"

