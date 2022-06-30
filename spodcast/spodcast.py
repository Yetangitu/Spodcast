from getpass import getpass
import glob
import hashlib
from logging import Logger
import logging
import os
import os.path
import random
import requests
import sys
import time

from librespot.audio.decoders import VorbisOnlyAudioQuality
from librespot.core import Session

from spodcast.config import Config
from spodcast.const import CREDENTIALS_PREFIX, TYPE, USER_READ_EMAIL, OFFSET, LIMIT
from spodcast.feedgenerator import RSS_FEED_FILE_NAME, RSS_INDEX_CODE, get_index_version

class Spodcast:    
    SESSION: Session = None
    DOWNLOAD_QUALITY = None
    CONFIG: Config = Config()
    LOG: Logger = None

    def __init__(self, args):
        Spodcast.CONFIG.load(args)
        logging.basicConfig(level=Spodcast.CONFIG.get_log_level())
        log = logging.getLogger(__name__)
        Spodcast.LOG = log
        log.debug("args: %s", args)
        if args.prepare_feed is True:
            root_path=Spodcast.CONFIG.get_root_path()
            os.makedirs(root_path, exist_ok=True)
            if os.path.exists(root_path):
                index_file_name = os.path.join(root_path, RSS_FEED_FILE_NAME)
                if not os.path.isfile(index_file_name) or int(get_index_version(index_file_name)) < Spodcast.CONFIG.get_version_int():
                    rss_file = open(index_file_name, "w")
                    rss_file.write(RSS_INDEX_CODE(Spodcast.CONFIG.get_bin_path(), os.path.basename(Spodcast.CONFIG.get_config_path()), Spodcast.CONFIG.get_version_str()))
                    rss_file.close()
            else:
                sys.exit(f"Can not create root path {root_path}")

        if args.login:
            filename = args.login
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as file:
                    for line in file.readlines():
                        Spodcast.account(line.strip())
                sys.exit(0)
            else:
                sys.exit(f"Can not read username/password file {filename}")

        Spodcast.login()

    @classmethod
    def account(cls, line):
        cred_directory = Config.get_config_dir()
        if os.path.isdir(cred_directory):
            (username,password) = line.split()
            cred_filename = CREDENTIALS_PREFIX + "-" + hashlib.md5(username.encode('utf-8'),usedforsecurity=False).hexdigest() + ".json"
            cred_location = os.path.join(cred_directory, cred_filename)
            conf = Session.Configuration.Builder().set_stored_credential_file(cred_location).build()
            session = Session.Builder(conf).user_pass(username, password).create()
            if not session.is_valid():
                Spodcast.LOG.error("Invalid username/password for username " + username);
             
    @classmethod
    def login(cls):
        cred_directory = Config.get_config_dir()
        credfiles = glob.glob(os.path.join(cred_directory, CREDENTIALS_PREFIX) + "-*.json")
        if credfiles:
            random.shuffle(credfiles)
            for credfile in credfiles:
                try:
                    cred_location = os.path.join(cred_directory, credfile)
                    conf = Session.Configuration.Builder().set_stored_credential_file(cred_location).set_store_credentials(False).build()
                    session = Session.Builder(conf).stored_file().create()
                    if session.is_valid():
                        cls.SESSION = session
                        return
                    else:
                        Spodcast.LOG.warning(f"Invalid credentials in {cred_location}")
                except RuntimeError:
                    Spodcast.LOG.error("RuntimeError")
                    pass
                
        cred_location = Config.get_credentials_location()

        if os.path.isfile(cred_location):
            try:
                conf = Session.Configuration.Builder().set_stored_credential_file(cred_location).set_store_credentials(False).build()
                cls.SESSION = Session.Builder(conf).stored_file().create()
                return
            except RuntimeError:
                pass
        while True:
            user_name = ''
            while len(user_name) == 0:
                user_name = input('Username: ')
            password = getpass()
            try:
                conf = Session.Configuration.Builder().set_stored_credential_file(cred_location).build()
                cls.SESSION = Session.Builder(conf).user_pass(user_name, password).create()
                return
            except RuntimeError:
                pass

    @classmethod
    def get_content_stream(cls, content_id, quality):
        return cls.SESSION.content_feeder().load(content_id, VorbisOnlyAudioQuality(quality), False, None)

    @classmethod
    def __get_auth_token(cls):
        return cls.SESSION.tokens().get_token(USER_READ_EMAIL).access_token

    @classmethod
    def get_auth_header(cls):
        return {
            'Authorization': f'Bearer {cls.__get_auth_token()}',
            'Accept-Language': f'{cls.CONFIG.get_language()}'
        }

    @classmethod
    def get_auth_header_and_params(cls, limit, offset):
        return {
            'Authorization': f'Bearer {cls.__get_auth_token()}',
            'Accept-Language': f'{cls.CONFIG.get_language()}'
        }, {LIMIT: limit, OFFSET: offset}

    @classmethod
    def invoke_url_with_params(cls, url, limit, offset, **kwargs):
        headers, params = cls.get_auth_header_and_params(limit=limit, offset=offset)
        params.update(kwargs)
        return requests.get(url, headers=headers, params=params).json()

    @classmethod
    def invoke_url(cls, url, tryCount=0):
        headers = cls.get_auth_header()
        Spodcast.LOG.debug(headers)
        response = requests.get(url, headers=headers)
        responsetext = response.text
        responsejson = response.json()

        if 'error' in responsejson:
            if tryCount < (cls.CONFIG.get_retry() - 1):
                Spodcast.LOG.warning(f"Spotify API Error (try {tryCount + 1}) ({responsejson['error']['status']}): {responsejson['error']['message']}")
                time.sleep(5)
                return cls.invoke_url(url, tryCount + 1)

            Spodcast.LOG.error(f"Spotify API Error ({responsejson['error']['status']}): {responsejson['error']['message']}")

        return responsetext, responsejson
