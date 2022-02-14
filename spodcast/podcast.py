import json
import logging
import os
import time
from html import escape
import urllib.parse

from librespot.metadata import EpisodeId

from spodcast.const import ERROR, ID, ITEMS, NAME, SHOW, DURATION_MS, DESCRIPTION, RELEASE_DATE, URI, URL, EXTERNAL_URLS, IMAGES, SPOTIFY, FILE_EXISTS
from spodcast.feedgenerator import RSS_FEED_CODE, RSS_FEED_FILE_NAME, RSS_FEED_SHOW_INDEX, RSS_FEED_INFO_EXTENSION
from spodcast.spotapi import EPISODE_INFO_URL, SHOWS_URL, EPISODE_DOWNLOAD_URL, ANON_PODCAST_DOMAIN
from spodcast.utils import clean_filename
from spodcast.spodcast import Spodcast

log = logging.getLogger(__name__)

def get_info(episode_id_str, target="episode"):
    log.info("Fetching episode information...")
    (raw, info) = Spodcast.invoke_url(f'{EPISODE_INFO_URL}/{episode_id_str}')
    if not info:
        log.error('INVALID EPISODE ID')

    log.debug("episode info: %s", info)

    if ERROR in info:
        return None, None

    if target == "episode":

        podcast_name = info[SHOW][NAME]
        episode_name = info[NAME]
        duration_ms = info[DURATION_MS]
        description = info[DESCRIPTION]
        release_date = info[RELEASE_DATE]
        uri = info[URI]

        return podcast_name, duration_ms, episode_name, description, release_date, uri

    elif target == "show":
        podcast_name = info[SHOW][NAME]
        link = info[SHOW][EXTERNAL_URLS][SPOTIFY]
        description = info[SHOW][DESCRIPTION]
        image = info[SHOW][IMAGES][0][URL]

        return podcast_name, link, description, image


def get_show_episodes(show_id_str) -> list:
    episodes = []
    offset = 0
    limit = 50

    log.info("Fetching episodes...")
    while True:
        resp = Spodcast.invoke_url_with_params(
            f'{SHOWS_URL}/{show_id_str}/episodes', limit=limit, offset=offset)
        offset += limit
        for episode in resp[ITEMS]:
            episodes.append(episode[ID])
        if len(resp[ITEMS]) < limit:
            break

    return episodes


def download_file(url, filepath):
    import functools
    import pathlib
    import shutil
    import requests

    r = requests.get(url, stream=True, allow_redirects=True)
    if r.status_code != 200:
        r.raise_for_status()  # Will only raise for 4xx codes, so...
        log.error(f"Request to {url} returned status code {r.status_code}")
        return

    file_size = int(r.headers.get('Content-Length', 0))

    if (
        os.path.isfile(filepath)
        and abs(file_size - os.path.getsize(filepath)) < 1000
        and Spodcast.CONFIG.get_skip_existing_files()
    ):
        return filepath, FILE_EXISTS

    log.info("Downloading file")
    r.raw.read = functools.partial(r.raw.read, decode_content=True)
    with open(filepath, "wb") as file:
        shutil.copyfileobj(r.raw, file)

    return filepath, os.path.getsize(filepath)

def download_stream(stream, filepath):
    size = stream.input_stream.size

    if (
        os.path.isfile(filepath)
        and abs(size - os.path.getsize(filepath)) < 1000
        and Spodcast.CONFIG.get_skip_existing_files()
    ):
        return filepath, FILE_EXISTS
 
    log.info("Downloading stream")
    time_start = time.time()
    downloaded = 0
    with open(filepath, 'wb') as file:
        for _ in range(int(size / Spodcast.CONFIG.get_chunk_size()) + 1):
            data = stream.input_stream.stream().read(Spodcast.CONFIG.get_chunk_size())
            file.write(data)
            downloaded += len(data)
            if Spodcast.CONFIG.get_download_real_time():
                delta_real = time.time() - time_start
                delta_want = (downloaded / size) * (duration_ms/1000)
                log.debug(f"realtime enabled, waiting for {delta_real} seconds...")
                if delta_want > delta_real:
                    time.sleep(delta_want - delta_real)

    return filepath, downloaded


def download_episode(episode_id) -> None:
    podcast_name, duration_ms, episode_name, description, release_date, uri = get_info(episode_id, "episode")

    if podcast_name is None:
        log.warning('Skipping episode (podcast NOT FOUND)')
    elif episode_name is None:
        log.warning('Skipping episode (episode NOT FOUND)')
    else:
        filename = clean_filename(podcast_name + ' - ' + episode_name)
        download_url = Spodcast.invoke_url(EPISODE_DOWNLOAD_URL(episode_id))[1]["data"]["episode"]["audio"]["items"][-1]["url"]
        log.debug(f"download_url: {download_url}")
        show_directory = os.path.realpath(os.path.join(Spodcast.CONFIG.get_root_path(), clean_filename(podcast_name) + '/'))
        os.makedirs(show_directory, exist_ok=True)

        if ANON_PODCAST_DOMAIN in download_url:
            episode_stream_id = EpisodeId.from_base62(episode_id)
            stream = Spodcast.get_content_stream(episode_stream_id, Spodcast.DOWNLOAD_QUALITY)
            basename = f"{filename}.ogg"
            filepath = os.path.join(show_directory, basename)
            path, size = download_stream(stream, filepath)
            mimetype="audio/ogg"
        else:
            basename=f"{filename}.mp3"
            filepath = os.path.join(show_directory, basename)
            path, size = download_file(download_url, filepath)
            mimetype="audio/mpeg"

        if size == FILE_EXISTS:
            log.info(f"Skipped {podcast_name}: {episode_name}")
            return
        else:
            log.warning(f"Downloaded {podcast_name}: {episode_name}")

        if Spodcast.CONFIG.get_enable_rss_feed():
            episode_info = {
                    "mimetype": mimetype,
                    "medium": "audio",
                    "duration": int(duration_ms/1000),
                    "date": time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.strptime(release_date, "%Y-%m-%d")),
                    "title": escape(episode_name), "guid": uri, "description": escape(description),
                    "filename": urllib.parse.quote(basename),
                    "size": int(size) }
            info_file = open(os.path.join(show_directory, f"{basename}.{RSS_FEED_INFO_EXTENSION}"), "w")
            info_file.write(json.dumps(episode_info))
            info_file.close()

            show_index_file_name = os.path.join(show_directory, f"{RSS_FEED_SHOW_INDEX}.{RSS_FEED_INFO_EXTENSION}")
            if not os.path.isfile(show_index_file_name):
                podcast_name, link, description, image = get_info(episode_id, "show")
                show_info = {
                        "title": escape(podcast_name),
                        "link": link,
                        "description": escape(description),
                        "image": image }
                show_index_file = open(show_index_file_name, "w")
                show_index_file.write(json.dumps(show_info))
                show_index_file.close()

            rss_file_name = os.path.join(show_directory, RSS_FEED_FILE_NAME)
            if not os.path.isfile(rss_file_name):
                rss_file = open(rss_file_name, "w")
                rss_file.write(RSS_FEED_CODE())
                rss_file.close()

