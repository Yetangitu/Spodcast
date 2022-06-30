import logging

from itertools import islice
from librespot.audio.decoders import AudioQuality
from librespot.metadata import ShowId, EpisodeId

from spodcast.podcast import download_episode, get_episodes
from spodcast.utils import regex_input_for_urls
from spodcast.spodcast import Spodcast

log = logging.getLogger(__name__)

def client(args) -> None:
    Spodcast(args)
    Spodcast.DOWNLOAD_QUALITY = AudioQuality.NORMAL

    if args.urls:
        for spotify_url in args.urls:
            episode_id_str, show_id_str = regex_input_for_urls(spotify_url)
            log.debug(f"episode_id_str {episode_id_str}. show_id_str {show_id_str}")
            if episode_id_str is not None:
                episode_id = EpisodeId.from_base62(episode_id_str).hex_id()
                log.debug("episode_id: %s", episode_id)
                download_episode(episode_id)
            elif show_id_str is not None:
                show_id = ShowId.from_base62(show_id_str)
                log.debug("show_id: %s", show_id)
                for episode_id in islice(get_episodes(show_id), Spodcast.CONFIG.get_max_episodes()):
                    log.debug("episode_id: %s", episode_id)
                    download_episode(episode_id)
