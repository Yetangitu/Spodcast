import json
import logging
import os
import time
from datetime import datetime
from html import escape
import urllib.parse

import base62
from base62 import CHARSET_INVERTED
import ffmpeg

from librespot import util
from librespot.metadata import ShowId, EpisodeId
from librespot.core import ApiClient

from spodcast.const import FILE_EXISTS, IMAGE_CDN
from spodcast.feedgenerator import RSS_FEED_CODE, RSS_FEED_FILE_NAME, RSS_FEED_SHOW_INDEX, RSS_FEED_INFO_EXTENSION, RSS_FEED_SHOW_IMAGE, RSS_FEED_VERSION, get_index_version
from spodcast.utils import clean_filename, uri_to_url
from spodcast.spodcast import Spodcast

log = logging.getLogger(__name__)


def hex_to_spotify_id(hex_id):
    return base62.encodebytes(util.hex_to_bytes(hex_id), CHARSET_INVERTED)


def get_show_info(show_id_hex):
    log.info("Fetching show information...")
    show_id = ShowId.from_hex(show_id_hex)
    uri = f'spotify:show:{hex_to_spotify_id(show_id_hex)}'
    info = Spodcast.SESSION.api().get_metadata_4_show(show_id)
    link = uri_to_url(uri)
    description = info.description
    image = IMAGE_CDN(util.bytes_to_hex(info.cover_image.image[1].file_id))

    return link, description, image


def get_episode_info(episode_id_hex):
    log.info("Fetching episode information...")
    episode_id = EpisodeId.from_hex(episode_id_hex)
    uri = f'spotify:episode:{hex_to_spotify_id(episode_id_hex)}'
    info = Spodcast.SESSION.api().get_metadata_4_episode(episode_id)
    podcast_name = info.show.name
    podcast_id = util.bytes_to_hex(info.show.gid)
    episode_name = info.name
    duration_ms = info.duration
    description = info.description
    external_url = info.external_url if info.external_url else None
    pt = info.publish_time
    release_date = f'{pt.year}-{pt.month}-{pt.day}T{pt.hour}:{pt.minute}:00Z'

    return podcast_name, podcast_id, duration_ms, episode_name, description, release_date, uri, external_url


def get_episodes(show_id):
    info = Spodcast.SESSION.api().get_metadata_4_show(show_id)
    episodes = info.episode
    episodes.sort(key = lambda x: datetime.strptime(f'{x.publish_time.year}-{x.publish_time.month}-{x.publish_time.day}T{x.publish_time.hour}:{x.publish_time.minute}:00Z', "%Y-%m-%dT%H:%M:%SZ"), reverse=True)

    return [util.bytes_to_hex(episode.gid) for episode in episodes]


def download_file(url, filepath):
    import functools
    import pathlib
    import shutil
    import requests

    mimetype = "audio/mpeg"

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
        return filepath, FILE_EXISTS, mimetype

    log.info("Downloading file")
    r.raw.read = functools.partial(r.raw.read, decode_content=True)
    with open(filepath, "wb") as file:
        shutil.copyfileobj(r.raw, file)


    return filepath, os.path.getsize(filepath), mimetype


def download_stream(stream, filepath):
    size = stream.input_stream.size

    mp3_filepath = os.path.splitext(filepath)[0] + ".mp3"
    mimetype = "audio/ogg"

    if (
        # "FILE SIZE CHECK TEMPORARILY OUT OF ORDER"
        # Need to find a way to get decrypted content size
        # from Spotify to enable file size checks, for now
        # this only checks for the presence of a file with
        # the same name. To recover from failed downloads
        # simply remove incomplete files
        #
        #((os.path.isfile(filepath)
        #and abs(size - os.path.getsize(filepath)) < 1000)
        (os.path.isfile(filepath)
        or (Spodcast.CONFIG.get_transcode()
        and os.path.isfile(mp3_filepath)))
        and Spodcast.CONFIG.get_skip_existing_files()
    ):
        return filepath, FILE_EXISTS, mimetype
 
    log.info("Downloading stream")
    time_start = time.time()
    downloaded = 0
    with open(filepath, 'wb') as file:
        data = b""
        while data := stream.input_stream.stream().read(Spodcast.CONFIG.get_chunk_size()):
            if data == b"":
                break
            file.write(data)
            downloaded += len(data)
            if Spodcast.CONFIG.get_download_real_time():
                delta_real = time.time() - time_start
                delta_want = (downloaded / size) * (duration_ms/1000)
                log.debug(f"realtime enabled, waiting for {delta_real} seconds...")
                if delta_want > delta_real:
                    time.sleep(delta_want - delta_real)

    if Spodcast.CONFIG.get_transcode():
        log.info("transcoding ogg->mp3")
        transcoder = ffmpeg.input(filepath)
        transcoder = ffmpeg.output(transcoder, mp3_filepath)
        ffmpeg.run(transcoder, quiet=True)
        file.close()
        os.unlink(filepath)
        filepath = mp3_filepath
        downloaded = os.path.getsize(filepath)
        mimetype = "audio/mpeg"

    return filepath, downloaded, mimetype


def download_episode(episode_id) -> None:
    try:
        podcast_name, podcast_id, duration_ms, episode_name, description, release_date, uri, download_url = get_episode_info(episode_id)

        if podcast_name is None:
            log.warning('Skipping episode (podcast NOT FOUND)')
        elif episode_name is None:
            log.warning('Skipping episode (episode NOT FOUND)')
        else:
            filename = clean_filename(podcast_name + ' - ' + episode_name)
            show_directory = os.path.realpath(os.path.join(Spodcast.CONFIG.get_root_path(), clean_filename(podcast_name) + '/'))
            os.makedirs(show_directory, exist_ok=True)

            if download_url is None:
                episode_stream_id = EpisodeId.from_hex(episode_id)
                stream = Spodcast.get_content_stream(episode_stream_id, Spodcast.DOWNLOAD_QUALITY)
                basename = f"{filename}.ogg"
                filepath = os.path.join(show_directory, basename)
                path, size, mimetype = download_stream(stream, filepath)
                basename = os.path.basename(path) # may have changed due to transcoding
            else:
                basename=f"{filename}.mp3"
                filepath = os.path.join(show_directory, basename)
                path, size, mimetype = download_file(download_url, filepath)

            if size == FILE_EXISTS:
                log.info(f"Skipped {podcast_name}: {episode_name}")
            else:
                log.warning(f"Downloaded {podcast_name}: {episode_name}")

                if Spodcast.CONFIG.get_rss_feed():
                    episode_info = {
                            "mimetype": mimetype,
                            "medium": "audio",
                            "duration": int(duration_ms/1000),
                            "date": time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.strptime(release_date, "%Y-%m-%dT%H:%M:%SZ")),
                            "title": escape(episode_name), "guid": uri, "description": escape(description),
                            "filename": urllib.parse.quote(basename),
                            "size": int(size) }
                    info_file = open(os.path.join(show_directory, f"{basename}.{RSS_FEED_INFO_EXTENSION}"), "w")
                    info_file.write(json.dumps(episode_info))
                    info_file.close()

            if Spodcast.CONFIG.get_rss_feed():
                show_index_file_name = os.path.join(show_directory, f"{RSS_FEED_SHOW_INDEX}.{RSS_FEED_INFO_EXTENSION}")
                if not os.path.isfile(show_index_file_name) or int(get_index_version(show_index_file_name)) < Spodcast.CONFIG.get_version_int():
                    podcast_link, podcast_description, podcast_image = get_show_info(podcast_id)
                    show_info = {}
                    if os.path.isfile(show_index_file_name):
                        with open(show_index_file_name, encoding='utf-8') as file:
                            show_info = json.load(file)
                            file.close()
                    show_info["version"] = str(RSS_FEED_VERSION + Spodcast.CONFIG.get_version_str())
                    show_info["title"] = escape(podcast_name)
                    show_info["link"] = podcast_link
                    show_info["description"] = escape(podcast_description)
                    show_info["image"] = RSS_FEED_SHOW_IMAGE 
                    show_index_file = open(show_index_file_name, "w")
                    show_index_file.write(json.dumps(show_info))
                    show_index_file.close()

                show_image_name = os.path.join(show_directory, f"{RSS_FEED_SHOW_IMAGE}")
                if not os.path.isfile(show_image_name):
                    download_file(podcast_image, show_image_name)

                rss_file_name = os.path.join(show_directory, RSS_FEED_FILE_NAME)
                if not os.path.isfile(rss_file_name) or int(get_index_version(rss_file_name)) < Spodcast.CONFIG.get_version_int():
                    rss_file = open(rss_file_name, "w")
                    rss_file.write(RSS_FEED_CODE(Spodcast.CONFIG.get_version_str()))
                    rss_file.close()

    except ApiClient.StatusCodeException as status:
        log.warning("episode %s, StatusCodeException: %s", episode_id, status)
