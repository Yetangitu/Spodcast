import json
import os
import pkg_resources
import sys
from typing import Any

CONFIG_FILE_PATH = '../spodcast.json'

CONFIG_DIR = 'CONFIG_DIR'
CONFIG_PATH = 'CONFIG_PATH'
VERSION = 'VERSION'
VERSION_STR = pkg_resources.require("Spodcast")[0].version

ROOT_PATH = 'ROOT_PATH'
SKIP_EXISTING_FILES = 'SKIP_EXISTING_FILES'
CHUNK_SIZE = 'CHUNK_SIZE'
DOWNLOAD_REAL_TIME = 'DOWNLOAD_REAL_TIME'
LANGUAGE = 'LANGUAGE'
CREDENTIALS_LOCATION = 'CREDENTIALS_LOCATION'
RETRY = 'RETRY'
MAX_EPISODES = 'MAX_EPISODES'
LOG_LEVEL = 'LOG_LEVEL'
RSS_FEED = 'RSS_FEED'
TRANSCODE = 'TRANSCODE'

CONFIG_VALUES = {
    ROOT_PATH:            { 'default': '../Spodcast/',
                            'type': str,
                            'arg': '--root-path',
                            'help': 'set root path for podcast cache' },
    SKIP_EXISTING_FILES:  { 'default': 'True',
                            'type': bool,
                            'arg': '--skip-existing',
                            'help': '[yes|no] skip files with the same name and size. Defaults to "yes".' },
    RETRY:                { 'default': 5,
                            'type': int,
                            'arg': '--retry',
                            'help': 'retry count for Spotify API access' },
    MAX_EPISODES:         { 'default': 1000,
                            'type': int,
                            'arg': '--max-episodes',
                            'help': 'number of episodes to download' },
    CHUNK_SIZE:           { 'default': 50000,
                            'type': int,
                            'arg': '--chunk-size',
                            'help': 'download chunk size' },
    DOWNLOAD_REAL_TIME:   { 'default': 'False',
                            'type': bool,
                            'arg': '--download-real-time',
                            'help': 'simulate streaming client' },
    LANGUAGE:             { 'default': 'en',
                            'type': str,
                            'arg': '--language',
                            'help': 'preferred content language' },
    CREDENTIALS_LOCATION: { 'default': 'credentials.json',
                            'type': str,
                            'arg': '--credentials-location',
                            'help': 'path to credentials file. If a relative path is used the file will be stored in the same directory as the configuration file (-c /path/to/config.json -> /path/to).' },
    RSS_FEED:             { 'default': 'True',
                            'type': bool,
                            'arg': '--rss-feed',
                            'help': '[yes|no] add a (php) RSS feed server and related metadata for feed. To manage feeds, point a web server at the spodcast root path as configured using --root-path. Defaults to "yes".' },
    TRANSCODE:            { 'default': 'False',
                            'type': bool,
                            'arg': '--transcode',
                            'help': '[yes|no] transcode ogg/vorbis to mp3 (where applicable) - only needed for devices which do not support open formats (e.g. iOS). Defaults to "no".' },
    LOG_LEVEL:            { 'default': 'warning',
                            'type': str,
                            'arg': '--log-level',
                            'help': 'log level (debug/info/warning/error/critical)' }
}

class Config:
    Values = {}

    @classmethod
    def load(cls, args) -> None:
        app_dir = os.path.dirname(__file__)
        dump_config=False

        config_fp = CONFIG_FILE_PATH
        if args.config_location:
            config_fp = args.config_location

        true_config_file_path = os.path.join(app_dir, config_fp)

        # Load config from spodcast.json

        if not os.path.exists(true_config_file_path):
            dump_config=True
            os.makedirs(os.path.dirname(true_config_file_path), exist_ok=True)
            cls.Values = cls.get_default_json()
        else:
            with open(true_config_file_path, encoding='utf-8') as config_file:
                jsonvalues = json.load(config_file)
                cls.Values = {}
                for key in CONFIG_VALUES:
                    if key in jsonvalues:
                        cls.Values[key] = cls.parse_arg_value(key, jsonvalues[key])

        # Add default values for missing keys

        for key in CONFIG_VALUES:
            if key not in cls.Values:
                cls.Values[key] = cls.parse_arg_value(key, CONFIG_VALUES[key]['default'])
                dump_config=True

        # Override config from commandline arguments

        for key in CONFIG_VALUES:
            if key.lower() in vars(args) and vars(args)[key.lower()] is not None:
                cls.Values[key] = cls.parse_arg_value(key, vars(args)[key.lower()])

        # dump current config to config file

        if dump_config:
            with open(true_config_file_path, 'w', encoding='utf-8') as config_file:
                json.dump(cls.get_config_json(), config_file, indent=4)

        # these values should not be overriden

        cls.Values[CONFIG_DIR] = os.path.dirname(true_config_file_path)
        cls.Values[CONFIG_PATH] = str(true_config_file_path)
        cls.Values[VERSION] = str(VERSION_STR)

    @classmethod
    def get_default_json(cls) -> Any:
        r = {}
        for key in CONFIG_VALUES:
            r[key] = CONFIG_VALUES[key]['default']
        return r

    @classmethod
    def get_config_json(cls) -> Any:
        r = {}
        for key in CONFIG_VALUES:
            r[key]=cls.Values[key]
        return r

    @classmethod
    def parse_arg_value(cls, key: str, value: Any) -> Any:
        if type(value) == CONFIG_VALUES[key]['type']:
            return value
        if CONFIG_VALUES[key]['type'] == str:
            return str(value)
        if CONFIG_VALUES[key]['type'] == int:
            return int(value)
        if CONFIG_VALUES[key]['type'] == bool:
            if str(value).lower() in ['yes', 'true', '1']:
                return True
            if str(value).lower() in ['no', 'false', '0']:
                return False
            raise ValueError("Not a boolean: " + value)
        raise ValueError("Unknown Type: " + value)

    @classmethod
    def get(cls, key: str) -> Any:
        return cls.Values.get(key)

    @classmethod
    def get_config_dir(cls) -> str:
        return cls.get(CONFIG_DIR)

    @classmethod
    def get_root_path(cls) -> str:
        return os.path.join(os.path.dirname(__file__), cls.get(ROOT_PATH))

    @classmethod
    def get_skip_existing_files(cls) -> bool:
        return cls.get(SKIP_EXISTING_FILES)

    @classmethod
    def get_chunk_size(cls) -> int:
        return cls.get(CHUNK_SIZE)

    @classmethod
    def get_language(cls) -> str:
        return cls.get(LANGUAGE)

    @classmethod
    def get_download_real_time(cls) -> bool:
        return cls.get(DOWNLOAD_REAL_TIME)

    @classmethod
    def get_credentials_location(cls) -> str:
        credentials_location = cls.get(CREDENTIALS_LOCATION)
        return credentials_location if os.path.isabs(credentials_location) else os.path.join(cls.get(CONFIG_DIR), cls.get(CREDENTIALS_LOCATION))

    @classmethod
    def get_retry(cls) -> int:
        return cls.get(RETRY)

    @classmethod
    def get_max_episodes(cls) -> int:
        return cls.get(MAX_EPISODES)

    @classmethod
    def get_rss_feed(cls) -> bool:
        return cls.get(RSS_FEED)

    @classmethod
    def get_transcode(cls) -> bool:
        return cls.get(TRANSCODE)

    @classmethod
    def get_log_level(cls) -> str:
        return str(cls.get(LOG_LEVEL)).upper()

    @classmethod
    def get_bin_path(cls) -> str:
        return str(sys.argv[0])

    @classmethod
    def get_config_path(cls) -> str:
        return cls.get(CONFIG_PATH)

    @classmethod
    def get_version_str(cls) -> str:
        return cls.get(VERSION)

    @classmethod
    def get_version_int(cls) -> int:
        return int(cls.get(VERSION).replace('.',''))
