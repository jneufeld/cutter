# ==============================================================================
# run.py
#
# Used to run an Armada instance. Be sure to look over the example config file
# and provide one at runtime.
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import json
from sys import exit, argv

from Armada import Armada
from MySQLConnector import MySQLConnector
from SubredditWallpaperCrawler import SubredditWallpaperCrawler


# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def usage():
    """
    Prints the usage string.
    """
    print 'python run.py <config_file.json>'

def check_args(argv):
    """
    Check the args are as expected, if not, print usage and exit.
    """
    if len(argv) != 2:
        usage()
        exit()

def get_settings(config_file):
    """
    Gets the configuration settings as a JSON blob from a file.

    Arguments:
        config_file<string> -- File name to read from.

    Returns:
        JSON blob of configuration settings.
    """
    result = None

    try:
        raw_settings = open(config_file).read()
        result = json.loads(raw_settings)
    except Exception as error:
        print 'Unable to load settings file: %s' % config_file
        exit()

    return result

def make_armada(settings):
    """
    Create and return an Armada instance.

    Arguments:
        settings -- JSON blob of all config settings.

    Returns:
        An Armada instance created with the given settings.
    """
    result = None

    try:
        armada_settings = settings['armada']
        result = Armada(pause=armada_settings['crawl_pause'])
    except Exception as error:
        print 'Unable to create Armada instance. Details:\n%s' % error
        exit()

    return result 

def make_db_connector(settings):
    """
    Create a database connector.

    Arguments:
        settings -- JSON blob of all config settings.

    Returns:
        A MySQL database connector with the config settings.
    """
    result = None

    try:
        db_settings = settings['database']
        result = MySQLConnector(db_settings['database_name'],
            db_settings['username'],
            db_settings['password'],
            db_settings['wallpaper_table'],
            db_settings['keyword_table'],
            db_settings['host'])
    except Exception as error:
        print 'Unable to create DB connector. Details:\n%s' % error
        exit()

    return result

def setup_crawlers(settings, armada, db_connector):
    """
    Create and setup crawlers specified by the settings file and set them up to
    run with the Armada and DB connector provided.

    Arguments:
        settings -- JSON blob of all config settings.
    """
    try:
        crawler_settings = settings['crawlers']

        for crawler in crawler_settings:
            crawler_type = crawler['type']

            if crawler_type == 'subreddit':
                subreddit = crawler['subreddit']
                item_limit = crawler['item_limit']
                cache_size = crawler['cache_size']

                sub_crawler = SubredditWallpaperCrawler(subreddit,
                    db_connector,
                    item_limit,
                    cache_size)
                armada.add_crawler(sub_crawler)
            else:
                print 'Unknown crawler type: %s. Continuing...' % crawler_type
    except Exception as error:
        print 'Unable to create crawler. Details: %s' % error
        exit()


# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    check_args(argv)
    settings = get_settings(argv[1])

    armada = make_armada(settings)
    db_connector = make_db_connector(settings)
    setup_crawlers(settings, armada, db_connector)

    armada.run()
