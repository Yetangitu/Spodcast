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

Another way of running Spodcast is by using the zipapp which can be downloaded from the `releases/X.Y.Z` directory, look for `spodcast.pyz` and make sure to get the latest version. Run the zipapp using `python spodcast.pyz`.

## Usage
To use Spodcast you need a (free) Spotify account, if you don't have one yet you'll need to take care of that first at https://www.spotify.com/se/signup/ . You'll also need a web server to serve the RSS feed(s), any server which supports PHP will do here. See [Web server requirements](#webserver) for more information on how to configure the server.

Here's `spodcast` displaying its help message:
```
$ spodcast -h
usage: spodcast [-h] [--config-location CONFIG_LOCATION] [--root-path ROOT_PATH]
        [--skip-existing-files SKIP_EXISTING_FILES] [--retry-attemps RETRY_ATTEMPS]
        [--max-episodes MAX_EPISODES] [--chunk-size CHUNK_SIZE]
        [--download-real-time DOWNLOAD_REAL_TIME] [--language LANGUAGE]
        [--credentials-location CREDENTIALS_LOCATION] [--enable-rss-feed ENABLE_RSS_FEED]
        [--log-level LOG_LEVEL] urls ...

A caching Spotify podcast to RSS proxy.

positional arguments:
  urls                  Download podcast episode(s) from a url. Can take multiple urls.

optional arguments:
  -h, --help            show this help message and exit
  --config-location CONFIG_LOCATION
                        Specify the spodcast.json location
  --root-path ROOT_PATH
                        set root path for podcast cache
  --skip-existing-files SKIP_EXISTING_FILES
                        skip files with the same name and size
  --retry-attemps RETRY_ATTEMPS
                        retry count for Spotify API access
  --max-episodes MAX_EPISODES
                        number of episodes to download
  --chunk-size CHUNK_SIZE
                        download chunk size
  --download-real-time DOWNLOAD_REAL_TIME
                        simulate streaming client
  --language LANGUAGE   preferred content language
  --credentials-location CREDENTIALS_LOCATION
                        path to credentials file
  --enable-rss-feed ENABLE_RSS_FEED
                        add a (php) RSS feed server and related metadata for feed. To serve the feed, point a web server at the spodcast root path as configured using --root-path.
  --log-level LOG_LEVEL
                        log level (debug/info/warning/error/critical)
```
### Using Spodcast to proxy a Spotify podcast feed
The following example shows how to use the `spodcast` command to create a feed with the last 20 episodes (`--max-episodes 20`) of _The Joe Rogan Experience_ podcast, this link for which can be found by using the Spotify web app - either copy it from the browser location bar or use _Share->Copy Show Link_ from the show menu (three dots next to the _Follow_ button). The feed will be created in the `/mnt/audio/spodcast` directory (`--root-path /mnt/audio/spodcast`). By using `--log-level warning` Spodcast will show which episodes have been cached, if no files are cached and assuming no errors occurred the program will not produce any output (which will keep `cron` from filling your mailbox).
```
spodcast --config-location ~/.config/spodcast/spodcast.json --credentials-location ~/.config/spodcast/credentials.json --root-path /mnt/audio/spodcast --log-level warning --max-episodes 20 https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk
```
If this is the first time `spodcast` was used it will ask for your Spotify account information (username and password), on subsequent invocations it will use stored credentials. Edit the stored config file (see `--config-location`) to reflect your preferences, any option set there can be temporarily overridden by using command line options.
Once the initial feed has been created it can be kept up to date by running the same command regularly. Assuming Spodcast is run daily (using `cron` or `Task Scheduler`) and depending on the show update frequency it makes sense to lower the `--max-episodes`, `2` or `3` is a good choice for most shows which have daily updates but sometimes publish more than one episode per day.

Point your RSS clients at the Spodcast feed URL for this show and you should see new episodes appear after they were published on Spotify and subsequently picked up on the next `spodcast` invocation. For the example given in the [Web server requirements](#webserver) example that URL would be `http://spodcast.example.org/The_Joe_Rogan_Experience`.

### Using Spodcast to download a single episode
Spodcast can also be used stand-alone (without the need for a web server) by either just ignoring the feed-related files (`.index.php`, `index.info` plus a `*.info` file for every episode) or by disabling the RSS feed using `--enable-rss-feed no` on the command line. To get single episode links use the Spotify web app and select _Share->Copy Episode Link_ from the episode menu (three dots in the top-right corner of the episode block). The following example shows `spodcast` ready to download a single episode:
```
spodcast --config-location ~/.config/spodcast/spodcast.json --enable-rss-feed no https://open.spotify.com/episode/2rYwwE7hcpgsDo9vRVHxAI?si=24fb00294b7f40db
```
## Web server configuration {#webserver}
Spodcast places a hidden `.index.php` file in the show directory which will produce an RSS feed based on the information found in all `*.info` files in that directory. Configure the server to serve that `.index.php` file as the site index. For _nginx_ the following should suffice to produce an unencrypted (HTTP) feed under the domain name `spodcast.example.org` given a feed root directory (as configured using `--root-path`) of `/mnt/audio/spodcast` with _php-fpm 7.4_ listening on `unix:/run/php/php7.4-fpm.sock`:
```
server {
        listen 80;
        listen [::]:80;
        server_name spodcast.example.org;

        root /mnt/audio/spodcast;

        index .index.php;

        location / {
                try_files $uri $uri/ =404;
        }

        location ~ \.php$ {
                include snippets/fastcgi-php.conf;
                fastcgi_pass unix:/run/php/php7.0-fpm.sock;
        }
}
```
Examples for other web servers can be found elsewhere.
