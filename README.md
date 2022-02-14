# Spodcast

Spodcast is a caching Spotify podcast to RSS proxy. Using Spodcast you can follow Spotify-hosted netcasts/podcasts using any player which supports RSS, thus enabling the use of older hardware which is not compatible with the Spotify (web) app. Spodcast consists of the main Spodcast application - a Python 3 command line tool - and a PHP-based RSS feed generator. It uses the librespot-python library to access the Spotift API. To use Spodcast you need a (free) Spotify account.
Spodcast only supports the Spotify podcast service, it does not interface with the music streaming service.

## How does it work

Spotify hosts podcasts through their proprietary API and does not offer an RSS feed, making it mandatory to use the Spotify (web) app to follow these shows which makes it impossible to follow Spotify-hosted shows on any device which does not support the Spotify (web) app. *Spodcast* solves this problem by creating an RSS feed out of data returned through the Spotify podcast API. This feed can be served by any web server which supports PHP. By running *Spodcast* through a task scheduler (*cron* on \*nix, *Task Scheduler* on Windows) the feed will be kept up to date without the need for intervention. Have a look at these glorious *ASCIIGraphs™* which should answer all unasked questions:

### Spodcast regularly queries Spotify for new episodes...
```
                  --------------
                 |task scheduler|
                  --------------
                        |             ___________
  -------   APIv1   ----V---         /           \
 |Spotify|- - - - >|Spodcast|------>| File system |
  -------           --------         \___________/
```
### You want to listen to an episode using your old, unsupported but still functional phone...
```
                                           _____         ............
   ___________          ----------        |     | . o O |bla bla bla.|
  /           \        |Web server|  RSS  | YOUR|        ````````````
 | File system |------>|  + PHP   |------>| OLD |
  \___________/         ----------        |PHONE|
                                          |_____|

```
Thus, by the simple expedient of using a piece of code which produces another piece of code which is used by yet another piece of code to speak to that old, creaky but still functional phone the latter is saved from early forced retirement. You can both feel virtuous for not adding another piece of waste to the pile, provident for not spending funds on a new device which does the same as the old one, smart for escaping the trap of planned obsolescence and whatever other emotion you prefer, including none whatsover.

## Installation

Spodcast can be installed from source by running `pip install .` from within the package root directory:
```shell
$ git clone https://github.com/Yetangitu/spodcast.git
$ cd spodcast
$ pip install .
```

Once installed this way it can be uninstalled using `pip uninstall spodcast` if so required.

## Usage
To use Spodcast you need a (free) Spotify account, if you don't have one yet you'll need to take care of that first at https://www.spotify.com/se/signup/ . If you plan to use the RSS proxy feature you'll also need a web server to serve the RSS feed(s), any server which supports PHP will do here. See [Web server requirements](#webserver) for more information on how to configure the server.

Here's `spodcast` displaying its help message:
```
$ spodcast -h
usage: spodcast [-h] [-c CONFIG_LOCATION] [-p] [-l LOGIN] [--root-path ROOT_PATH]
                [--skip-existing SKIP_EXISTING] [--retry RETRY]
                [--max-episodes MAX_EPISODES] [--chunk-size CHUNK_SIZE]
                [--download-real-time DOWNLOAD_REAL_TIME] [--language LANGUAGE]
                [--credentials-location CREDENTIALS_LOCATION] [--rss RSS]
                [--log-level LOG_LEVEL]
                [urls ...]

A caching Spotify podcast to RSS proxy.

positional arguments:
  urls                  Download podcast episode(s) from a url. Can take multiple urls.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_LOCATION, --config-location CONFIG_LOCATION
                        Specify the spodcast.json location
  -p, --prepare-feed    Installs RSS feed server code in ROOT_PATH.
  -l LOGIN, --login LOGIN
                        Reads username and password from file passed as argument and stores
                        credentials for later use.
  --root-path ROOT_PATH
                        set root path for podcast cache
  --skip-existing SKIP_EXISTING
                        skip files with the same name and size
  --retry RETRY         retry count for Spotify API access
  --max-episodes MAX_EPISODES
                        number of episodes to download
  --chunk-size CHUNK_SIZE
                        download chunk size
  --download-real-time DOWNLOAD_REAL_TIME
                        simulate streaming client
  --language LANGUAGE   preferred content language
  --credentials-location CREDENTIALS_LOCATION
                        path to credentials file
  --rss RSS             add a (php) RSS feed server and related metadata for feed. To serve
                        the feed, point a web server at the spodcast root path as configured
                        using --root-path.
  --log-level LOG_LEVEL
                        log level (debug/info/warning/error/critical)
```
### Using Spodcast to proxy Spotify podcasts to RSS
The following example shows how to use the `spodcast` command to prepare the feed root directory and add a Spotify account to be used. It specifies the configuration file to create (`-c /mnt/audio/podcast/spodcast.json`) and the root path where podcasts will be downloaded to (`--root-path /mnt/audio/spodcast`). The `-p` option tells _spodcast_ to prepare the RSS feed server in the root directory which will also be used to store the credential file created by the `-l spotify.rc` command. That `spotify.rc` file is a plain text file containing the username and password (separated by a single space character) to use to login to Spotify. It is only needed to create the stored credentials file(s) so it can be deleted once _Spotcast_ is up and running.
```
spodcast -c /mnt/audio/podcast/spodcast.json --root-path /mnt/audio/spodcast -p -l /home/exampleuser/spotify.rc
```
Configure the [Web server](#webserver) using the path given as root path (in this example that would be `/mnt/audio/spodcast`) as web root, making sure to exclude files with `.json` and `.info` extenstions to avoid leaking your Spotify credentials (even though these are stored in hashed form using hashed file names). Now point a browser at the site you configured for _Spodcast_ and you're ready to add the first show or episode. This is done easily by entering the Spotify show/episode url (e.g. `https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk` for _The Joe Rogan Experience_ for the whole show, `https://open.spotify.com/episode/2rYwwE7hcpgsDo9vRVHxAI?si=24fb00294b7f40db` for a specific episode, notice the `show` and `episode` parts of these links) and either hitting _Enter_ or clicking the _Add_ button. Spodcast will now create a directory under the given root path, add the `.index.php` RSS feed generator script and the `index.info` show info URL used by that script and the RSS manager script and whatever episode(s) you decided to sync.

Once the initial feed has been created it can be kept up to date by enabling the feed update service found in the _Settings_ menu. Select the update frequency and the start time and click _Update_, this will create a _cron_ job for the web server which will run the Spodcast manager script to update feeds. While the update frequency is configured for all shows simultaneously this is not the case for the number of episodes to _sync_ and the number to _keep_ in cache, these can be configured individually for each show. The idea here is that some shows may publish more than one episode between update intervals so by fetching the last X episodes on each update nothing will be missed. Episodes which have already been synced will not be synced again so no time or bandwidth is wasted. In the same vein the number of episodes to _keep_ can be configured to make sure your RSS clients have the opportunity to download these before they are rotated out of cache. Once more than X (being the value chosen for _keep_) episodes have been downloaded the oldest episodes will be deleted to keep the total no more than X.

Point your RSS clients at the Spodcast feed URL for this show and you should see new episodes appear after they were published on Spotify and subsequently picked up on the next update. For the example given in the [Web server requirements](#webserver) example that URL would be `http://spodcast.example.org/The_Joe_Rogan_Experience`.

### Using the Spodcasti CLI command to download a single episode
Spodcast can also be used stand-alone (without the need for a web server) by either just ignoring the feed-related files (`.index.php`, `index.info` plus a `*.info` file for every episode) or by disabling the RSS feed using `--rss no` on the command line. Instead of using the `-l spotify.rc` command to add _Spotify_ credentials it is possible to point _Spotcast_ at a single `credentials.json` file (which will be created if it does not exist yet`), `spotcast` wil ask for the username and password when needed. To get single episode links use the Spotify web app and select _Share->Copy Episode Link_ from the episode menu (three dots in the top-right corner of the episode block). The following example shows (an already configured instance of) `spodcast` ready to download a single episode:
```
spodcast -c ~/.config/spodcast/spodcast.json --credentials-location ~/.config/spodcast/credentials.json --rss no https://open.spotify.com/episode/2rYwwE7hcpgsDo9vRVHxAI?si=24fb00294b7f40db
```
Like in the previous example _Spodcast_ will create a directory under the root path with the same name as the show from which the episode is downloaded. The episode will be downloaded into this directory under a `SHOW_NAME_-__EPISODE_NAME.[ogg|mp3]` name. Point a mediaplayer of choice at this file to play the episode.
In "manual" mode _Spodcast_ does not do anything by itself, feeds can be kept up to date by running _Spotcast_ with the required settings for `--max-episodes` (which is the value used for _sync_ in the web UI) and the show URL. Here's how to update the _The Joe Rogan Experience_ show using the `spodcast` CLI command, syncing the last 3 episodes:
```
spodcast -c ~/.config/spodcast/spodcast.json --rss no --max-episodes 3 https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk`
```
## Web server configuration {#webserver}
Spodcast places a hidden `.index.php` file in the root path and each show directory. The one in the root directory is used to manage feeds while those in the show directories produce RSS feeds based on the information found in all `*.info` files in that directory. Configure the server to serve those `.index.php` files as index to make things work as intended. Don't forget to block all web access to files ending in `.json` and `.info` to make sure you Spotify credentials (which are stored in hashed form in files named `spodcast-cred-MD5_HASH_OF_SPOTIFY_USER_NAME.json` in the root path) can not be accessed. For _nginx_ the following should suffice to produce an unencrypted (HTTP) feed under the domain name `spodcast.example.org` given a feed root directory (as configured using `--root-path`) of `/mnt/audio/spodcast` with _php-fpm 7.4_ listening on `unix:/run/php/php7.4-fpm.sock`:
```
server {
        listen 80;
        listen [::]:80;
        server_name spodcast.example.org;

        root /mnt/audio/spodcast;

        index .index.php;

        # these files should not be accessible
        location ~\.(json|info)$ {
                deny all;
                return 404;
        }

        location / {
                try_files $uri $uri/ =404;
        }

        location ~ \.php$ {
                include snippets/fastcgi-php.conf;
                fastcgi_pass unix:/run/php/php7.4-fpm.sock;
        }
}
```
Examples for other web servers can be found elsewhere, this is basically a default PHP configuration with the only difference being that `.index.php` is a hidden file.
