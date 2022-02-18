FROM python:3-buster

COPY . /app
WORKDIR /app

RUN pip3 install .

ENTRYPOINT ["/usr/local/bin/spodcast"]
