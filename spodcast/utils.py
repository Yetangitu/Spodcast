import re
import string
import unicodedata
from enum import Enum
from typing import List, Tuple

from spodcast.spodcast import Spodcast
from spodcast.const import OPEN_SPOTIFY_URL

valid_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def regex_input_for_urls(search_input) -> Tuple[str, str, str, str, str, str]:
    episode_uri_search = re.search(
        r'^spotify:episode:(?P<EpisodeID>[0-9a-zA-Z]{22})$', search_input)
    episode_url_search = re.search(
        r'^(https?://)?open\.spotify\.com/episode/(?P<EpisodeID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )

    show_uri_search = re.search(
        r'^spotify:show:(?P<ShowID>[0-9a-zA-Z]{22})$', search_input)
    show_url_search = re.search(
        r'^(https?://)?open\.spotify\.com/show/(?P<ShowID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )
    if episode_uri_search is not None or episode_url_search is not None:
        episode_id_str = (episode_uri_search
                          if episode_uri_search is not None else
                          episode_url_search).group('EpisodeID')
    else:
        episode_id_str = None

    if show_uri_search is not None or show_url_search is not None:
        show_id_str = (show_uri_search
                       if show_uri_search is not None else
                       show_url_search).group('ShowID')
    else:
        show_id_str = None

    return episode_id_str, show_id_str


def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    for r in replace:
        filename = filename.replace(r,'_')

    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    return cleaned_filename

def uri_to_url(spotify_id):
    (spotify,sp_type,sp_id) = spotify_id.split(':')
    return f'https://{OPEN_SPOTIFY_URL}/{sp_type}/{sp_id}'
