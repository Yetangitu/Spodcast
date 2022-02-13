import logging

from itertools import islice
from librespot.audio.decoders import AudioQuality

from spodcast.podcast import download_episode, get_show_episodes
from spodcast.utils import regex_input_for_urls
from spodcast.spodcast import Spodcast

log = logging.getLogger(__name__)

def client(args) -> None:
    Spodcast(args)
    Spodcast.DOWNLOAD_QUALITY = AudioQuality.NORMAL

    if args.urls:
        for spotify_url in args.urls:
            episode_id, show_id = regex_input_for_urls(spotify_url)
            log.debug(f"episode_id {episode_id}. show_id {show_id}")
            if episode_id is not None:
                download_episode(episode_id)
            elif show_id is not None:
                for episode in islice(get_show_episodes(show_id), Spodcast.CONFIG.get_max_episodes()):
                    download_episode(episode)
