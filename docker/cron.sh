#!/usr/bin/env bash

## Set default cron schedule
[[ -n ${CRON_SCHEDULE} ]] || export CRON_SCHEDULE="0 0 * * Sun"

## Variables for /run.sh
[[ -n ${SPODCAST_ROOT} ]] || export SPODCAST_ROOT='/data'
[[ -n ${SPODCAST_HTML} ]] || export SPODCAST_HTML="${SPODCAST_ROOT}/html"
[[ -n ${SPODCAST_CONFIG_JSON} ]] || export SPODCAST_CONFIG_JSON="${SPODCAST_ROOT}/spodcast.json"
[[ -n ${SPOTIFY_CREDS_JSON} ]] || export SPOTIFY_CREDS_JSON="${SPODCAST_ROOT}/creds.json"
[[ -n ${SPOTIFY_RC_PATH} ]] || export SPOTIFY_RC_PATH="${SPODCAST_ROOT}/spotify.rc"
[[ -n ${SPOTIFY_PASSWORD} ]] || export creds_supplied='false'
[[ -n ${SPOTIFY_USERNAME} ]] || export creds_supplied='false'
[[ -n ${MAX_EPISODES} ]] || export MAX_EPISODES='10'
[[ -n ${LOG_LEVEL} ]] || export LOG_LEVEL='info'
[[ -n ${CHUNK_SIZE} ]] || export CHUNK_SIZE='50000'
[[ -n ${RSS_FEED} ]] || export RSS_FEED='yes'
[[ -n ${TRANSCODE} ]] || export TRANSCODE='no'
[[ -n ${LANGUAGE} ]] || export LANGUAGE='en'
[[ -n ${SKIP_EXISTING} ]] || export SKIP_EXISTING='yes'

[[ ${creds_supplied} == 'false' ]] \
    && echo 'Please set the SPOTIFY_USERNAME and SPOTIFY_PASSWORD variables. Exiting.' \
    && exit 1

## Setup cron
echo SHELL=/bin/bash > /tmp/cron
echo PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin >> /tmp/cron
echo "${CRON_SCHEDULE} SPODCAST_ROOT=\"${SPODCAST_ROOT}\" SPODCAST_HTML=\"${SPODCAST_HTML}\" SPODCAST_CONFIG_JSON=\"${SPODCAST_CONFIG_JSON}\" SPOTIFY_CREDS_JSON=\"${SPOTIFY_CREDS_JSON}\" SPOTIFY_RC_PATH=\"${SPOTIFY_RC_PATH}\" SPOTIFY_PASSWORD=\"${SPOTIFY_PASSWORD}\" SPOTIFY_USERNAME=\"${SPOTIFY_USERNAME}\" MAX_EPISODES=\"${MAX_EPISODES}\" LOG_LEVEL=\"${LOG_LEVEL}\" CHUNK_SIZE=\"${CHUNK_SIZE}\" RSS_FEED=\"${RSS_FEED}\" TRANSCODE=\"${TRANSCODE}\" LANGUAGE=\"${LANGUAGE}\" SKIP_EXISTING=\"${SKIP_EXISTING}\" /run.sh"  >> /tmp/cron

echo "* * * * * chown -R 101:101 ${SPODCAST_HTML}" >> /tmp/cron

crontab /tmp/cron
rm /tmp/cron

crond -l 0 -d 0 -f
