# ==============================================================================
# SubredditWallpaperCrawler.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import hashlib
import praw
from PIL import Image
import re
import StringIO
import urllib2


# ------------------------------------------------------------------------------
# Class
# ------------------------------------------------------------------------------

class SubredditWallpaperCrawler(object):
    """
    Crawls a subreddit for wallpapers and drops them to a database when one is
    found matching given criteria.
    """

    def __init__(self, subreddit_name, db_connector):
        """
        Creates a subreddit wallpaper crawler.

        Arguments:
            subreddit_name<string>       -- Name of the subreddit to crawl.
            db_connector<MySQLConnector> -- Database connection object.
        """
        self.subreddit_name = subreddit_name
        self.db_connector = db_connector

        self.submission_cache = [] # TODO: Class for this, a real queue
        self.cache_size = 10

        self.known_extensions = ['jpg', 'png']

        self.user_agent = 'cutter -- Wallpaper Scraper 0.1 -- /u/expat_one'
        reddit = praw.Reddit(user_agent=self.user_agent)
        self.subreddit = reddit.get_subreddit(self.subreddit_name)

    def crawl(self):
        """
        Crawls the subreddit, saving wallpapers as it goes.
        """
        submissions = self.subreddit.get_hot(limit=10)

        for submission in submissions:
            submission_id = submission.id

            if self.already_crawled(submission_id):
                continue

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
        self.db_connector.store(img, name, keywords, source, img_size)

    def already_crawled(self, submission_id):
        """
        Returns true if the given submission ID is in the cache of crawled
        submissions.

        Arguments:
            submission_id<string> -- ID of submission.

        Returns:
            True if the ID is in cache, else False.
        """
        result = False

        if submission_id in self.submission_cache:
            result = True
        else:
            if len(self.submission_cache) > self.cache_size:
                del self.submission_cache[0]
            self.submission_cache.append(submission_id)

        return result

    def get_image(self, url, recurse=True):
        """
        Get the image, either directory or by scanning the link to find it.

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
