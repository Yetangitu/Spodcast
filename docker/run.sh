#!/usr/bin/env bash

## If the following variables are not defined, set defaults
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

## If Spotify credentials were supplied, create ${SPODCAST_ROOT}/spotify.rc
[[ ${creds_supplied} == 'false' ]] || echo "${SPOTIFY_USERNAME} ${SPOTIFY_PASSWORD}" > ${SPODCAST_ROOT}/spotify.rc

## If no arguments were supplied, then use environment variables
if [[ -z "$@" ]]
then
	## If SPOTIFY_PODCAST_URLS is defined, then run Spodcast
	if [[ -n ${SPOTIFY_PODCAST_URLS} ]]
	then
		## If ${SPOTIFY_RC_PATH} file exists
		if [[ -e ${SPOTIFY_RC_PATH} ]]
		then
		# Login first and then run spodcast
			/usr/local/bin/spodcast \
				-c "${SPODCAST_CONFIG_JSON}" \
				--root-path "${SPODCAST_HTML}" \
				--log-level "${LOG_LEVEL}" \
				--credentials-location "${SPOTIFY_CREDS_JSON}" \
				-p -l ${SPOTIFY_RC_PATH} \
				&& /usr/local/bin/spodcast \
					-c ${SPODCAST_CONFIG_JSON} \
					--log-level ${LOG_LEVEL} \
					--max-episodes ${MAX_EPISODES} \
					"${SPOTIFY_PODCAST_URLS}"
		else
			echo "SPOTIFY_PODCAST_URLS is defined, but no credentials were detected. Please set the SPOTIFY_USERNAME and SPOTIFY_PASSWORD variables."
			exit 1
		fi
	## If SPOTIFY_PODCAST_URLS is not defined and no arguments were supplied, just show the help message
	else
		/usr/local/bin/spodcast --help	
	fi
fi

## If arguments were supplied, do not use environment variables
[[ -n $@ ]] && /usr/local/bin/spodcast "$@"
