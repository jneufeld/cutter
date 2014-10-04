# ==============================================================================
# SubredditWallpaperCrawler.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import hashlib
from PIL import Image
import praw
import re
import StringIO
import urllib2

from SubmissionCache import SubmissionCache


# ------------------------------------------------------------------------------
# Main class
# ------------------------------------------------------------------------------

class SubredditWallpaperCrawler(object):
    """
    Crawls a subreddit for wallpapers and drops them to a database when one is
    found matching given criteria.
    """

    def __init__(self, subreddit_name, db_connector, limit=25, cache_size=50):
        """
        Creates a subreddit wallpaper crawler.

        Arguments:
            subreddit_name<string>       -- Name of the subreddit to crawl.
            db_connector<MySQLConnector> -- Database connection object.
            limit<int>                   -- Max number of items to get during
                                            crawl.
            cache_size<int>              -- Size of previously crawled items
                                            cache.
        """
        self.ITEM_LIMIT = 50

        if not subreddit_name:
            raise Exception('Subreddit name cannot be empty.')
        if not db_connector:
            raise Exception('Database connector must be initialized.')
        if limit > self.ITEM_LIMIT:
            message = 'Cannot get more than %d items.' % self.ITEM_LIMIT
            raise Exception(message)

        self.subreddit_name = subreddit_name
        self.db_connector = db_connector
        self.submission_cache = SubmissionCache(cache_size)

        self.known_extensions = ['jpg', 'png']

        self.user_agent = 'cutter -- Wallpaper Scraper 0.1 -- /u/expat_one'

        try:
            reddit = praw.Reddit(user_agent=self.user_agent)
            self.subreddit = reddit.get_subreddit(self.subreddit_name)
        except Exception as error:
            print 'Unable to connect to Reddit. Details: %s' % error
            raise error

    def crawl(self):
        """
        Crawls the subreddit, saving wallpapers as it goes.
        """
        try:
            submissions = self.subreddit.get_hot(limit=10)

            for submission in submissions:
                submission_id = submission.id

                if self.submission_cache.has_item(submission_id):
                    continue
                else:
                    self.submission_cache.add(submission_id)

                url = submission.url
                image = self.get_image(url)

                if image != False:
                    source = submission.permalink
                    nsfw = True if submission.over_18 else False

                    name = hashlib.md5(url).hexdigest()[:10]
                    keywords = self.make_keywords(submission.title)
                    size = self.get_img_size(image)

                    if nsfw:
                        keywords.append('nsfw')

                    self.store(image, name, keywords, source, size)
        except Exception as error:
            print 'Crawling failed. Details: %s' % error

    def store(self, img, name, keywords, source, img_size):
        """
        Stores the image and its metadata to the database.

        Arguments:
            img<string>        -- The image to save.
            name<string>       -- Unique name of the image.
            keywords<[string]> -- List of keywords describing the image.
            source<string>     -- Absolute URL to the image source.
            img_size<string>   -- Dimensions of the image.
        """
        try:
            self.db_connector.store(img, name, keywords, source, img_size)
        except Exception as error:
            print 'Unable to save wallpaper. Details: %s' % error

    def get_image(self, url, recurse=True):
        """
        Get the image, either directly or by scanning the link to find it.

        Arguments:
            url<string>      -- Absolute URL to image or page hosting image.
            recurse<boolean> -- Optional. If true, recursively search.

        Returns:
            Image blob data, or False if unable to find image.
        """
        result = False

        image_extension = url[-3:]

        try:
            if image_extension in self.known_extensions:
                result = urllib2.urlopen(url).read()
            elif 'imgur.com/' in url:
                page_source = urllib2.urlopen(url).read()
                link_re = '(?P<base>i\.imgur\.com/\w+\.\w+)"'
                matches = re.search(link_re, page_source)
                image_url = 'http://' + matches.group('base')
                return self.get_image(image_url, False)
            else:
                print 'Not sure what to do with this URL: %s' % url
        except Exception as error:
            print 'Unable to get image: %s' % error

        return result

    def make_keywords(self, text):
        """
        Create a list of keywords and phrases using the given text.

        Arguments:
            text<string> -- Text to make keywords out of.

        Returns:
            List of strings, each string being a keyword or phrase.
        """
        result = []

        words = re.sub('\W', ' ', text.lower()).split()
        result = words # TODO: Remove common words, consider grouping phrases

        return result

    def get_img_size(self, image):
        """
        Finds the size of the image.

        Arguments:
            image<string> -- Raw text blob of the image.

        Returns:
            Tuple containing the width and height of the image.
        """
        data = StringIO.StringIO()
        data.write(image)
        data.seek(0)

        image_data = Image.open(data)

        return image_data.size

    def __repr__(self):
        name = ''

        if hasattr(self, 'subreddit_name'):
            name = self.subreddit_name
        else:
            name = 'Subreddit not initialized'

        return '<SubredditWallpaperCrawler: %s>' % name
