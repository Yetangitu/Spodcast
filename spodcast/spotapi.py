EPISODE_INFO_URL = 'https://api.spotify.com/v1/episodes'

SHOWS_URL = 'https://api.spotify.com/v1/shows'

EPISODE_DOWNLOAD_URL = lambda episode_id: f'https://api-partner.spotify.com/pathfinder/v1/query?operationName=getEpisode&variables={{"uri":"spotify:episode:{episode_id}"}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"224ba0fd89fcfdfb3a15fa2d82a6112d3f4e2ac88fba5c6713de04d1b72cf482"}}}}'

ANON_PODCAST_DOMAIN = 'anon-podcast.scdn.co'


