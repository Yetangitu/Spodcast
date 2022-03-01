import argparse
import pkg_resources

from spodcast.app import client
from spodcast.config import CONFIG_VALUES

def main():
    parser = argparse.ArgumentParser(prog='spodcast', description='A caching Spotify podcast to RSS proxy.')
    parser.add_argument('-c', '--config-location',
                        type=str,
                        help='Specify the spodcast.json location')

    parser.add_argument('-p', '--prepare-feed',
                       action='store_true',
                       help='Installs RSS feed server code in ROOT_PATH.')

    parser.add_argument('-v', '--version',
                       action='version',
                       version = '%(prog)s ' + pkg_resources.require("Spodcast")[0].version)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('urls',
                       type=str,
                       # action='extend',
                       default='',
                       nargs='*',
                       help='Download podcast episode(s) from a url. Can take multiple urls.')

    group.add_argument('-l', '--login',
                       type=str,
                       help='Reads username and password from file passed as argument and stores credentials for later use.')

    for configkey in CONFIG_VALUES:
        parser.add_argument(CONFIG_VALUES[configkey]['arg'],
                            type=str,
                            default=None,
                            help=CONFIG_VALUES[configkey]['help'])

    parser.set_defaults(func=client)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
