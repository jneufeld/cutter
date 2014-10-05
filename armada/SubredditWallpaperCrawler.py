# ==============================================================================
# SubredditWallpaperCrawler.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import hashlib
from nltk.corpus import stopwords
from PIL import Image
import praw
import re
import StringIO
import urllib2

from FileWriter import FileWriter
from SubmissionCache import SubmissionCache
from Wallpaper import Wallpaper


# ------------------------------------------------------------------------------
# Main class
# ------------------------------------------------------------------------------

class SubredditWallpaperCrawler(object):
    """
    Crawls a subreddit for wallpapers and drops them to a database when one is
    found matching given criteria.
    """

    def __init__(self, subreddit_name,
            db_connector,
            wallpaper_path,
            thumbnail_path,
            limit=25,
            cache_size=50):
        """
        Creates a subreddit wallpaper crawler.

        Arguments:
            subreddit_name<string>       -- Name of the subreddit to crawl.
            db_connector<MySQLConnector> -- Database connection object.
            wallpaper_path<string>       -- Filesystem path to where wallpapers
                                            are saved.
            limit<int>                   -- Max number of items to get during
                                            crawl.
            cache_size<int>              -- Size of previously crawled items
                                            cache.
        """
        self.ITEM_LIMIT = 50
        self.NAME_LENGTH = 10
        self.MIN_IMAGE_WIDTH = 1024
        self.MIN_IMAGE_HEIGHT = 768

        if not subreddit_name:
            raise Exception('Subreddit name cannot be empty.')
        if not db_connector:
            raise Exception('Database connector must be initialized.')
        if not wallpaper_path:
            raise Exception('Wallpaper path cannot be empty.')
        if limit > self.ITEM_LIMIT:
            message = 'Cannot get more than %d items.' % self.ITEM_LIMIT
            raise Exception(message)

        self.subreddit_name = subreddit_name
        self.db_connector = db_connector
        self.wallpaper_path = wallpaper_path
        self.thumbnail_path = thumbnail_path
        self.submission_cache = SubmissionCache(cache_size)
        self.item_limit = limit

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
        submissions = self.subreddit.get_hot(limit=self.item_limit)

        for submission in submissions:
            try:
                self.handle_submission(submission)
            except Exception as error:
                print 'Unable to handle submission. Details: %s' % error

    def handle_submission(self, submission):
        """
        Crawl an individual submission. Extract relevant information and
        possibly save the wallpaper.

        Arguments:
            submission -- Single subreddit submission.
        """
        submission_id = submission.id

        if self.submission_cache.has_item(submission_id):
            return
        else:
            self.submission_cache.add(submission_id)

        wallpaper = Wallpaper(submission.url)

        if wallpaper != None and self.good_size(wallpaper):
            keywords = self.make_keywords(submission.title)
            source = submission.permalink

            if submission.over_18:
                keywords.append('nsfw')

            self.store(wallpaper, keywords, source)

    def store(self, wallpaper, keywords, source):
        """
        Stores the image and thumbnail to the filesystem, and the metadata to
        the database.

        Arguments:
            wallpaper<Wallpaper> -- The wallpaper to save.
            keywords<[string]>   -- List of keywords describing the image.
            source<string>       -- Absolute URL to the image source.
        """
        try:
            wrote_image = self.write_blob(wallpaper.image,
                self.wallpaper_path,
                wallpaper.image_name)
            wrote_thumbnail = self.write_blob(wallpaper.thumbnail,
                self.thumbnail_path,
                wallpaper.image_name)

            if wrote_image and wrote_thumbnail:
                self.db_connector.store(self.wallpaper_path,
                    wallpaper.image_name,
                    keywords,
                    source,
                    (wallpaper.image_width, wallpaper.image_height))
        except Exception as error:
            print 'Unable to save wallpaper. Details: %s' % error
            self.rollback_write(self.wallpaper_path, wallpaper.name)
            self.rollback_write(self.thumbnail_path, wallpaper.name)

    def write_blob(self, blob, path, name):
        """
        Write the image blob and a thumbnail to the filesystem.

        Arguments:
            blob<string> -- Image blob.
            path<string> -- Absolute filesystem path to write to.
            name<string> -- Image name.

        Returns:
            True if image was successfully written, else False.
        """
        result = False

        writer = FileWriter()
        if not writer.file_exists(path + name):
            writer.write(blob, path, name)
            print 'Wrote %s to %s.' % (name, path)
            result = True
        else:
            print '%s already exists at %s. Skipping write.' % (name, path)

        return result

    def rollback_write(self, path, name):
        """
        Rollback a filesystem write. If the file does not exist, fail silently.

        Arguments:
            path<string> -- Absolute filesystem path to file.
            name<string> -- Image name.

        Returns:
            True if image was successfully removed, else False.
        """
        result = False

        writer = FileWriter()
        if writer.file_exists(path + name):
            writer.unwrite(path, name)
            print 'Rolled back write of %s at %s.' % (name, path)
            result = True

        return result

    def make_keywords(self, text):
        """
        Create a list of keywords and phrases using the given text.

        Arguments:
            text<string> -- Text to make keywords out of.

        Returns:
            List of strings, each string being a keyword or phrase.
        """
        # TODO:
        #   - Better way to get words, i.e. words with hyphens and apostrophes
        #   - Get bigrams and trigrams, i.e. phrases
        result = []

        all_words = re.sub('\W', ' ', text.lower()).split()
        meaningless = set(stopwords.words('english'))
        meaningful = [w for w in all_words if w not in meaningless]
        result = list(set(meaningful))

        return result

    def good_size(self, wallpaper):
        """
        Tests if the width and height of the wallpaper meet the minimum size
        requirements.

        Arguments:
            wallpaper<Wallpaper> -- Wallpaper to test size on.

        Returns:
            True if image meets minimum width and height requirements.
        """
        result = False

        width, height = wallpaper.image_width, wallpaper.image_height
        ratio = float(width) / height

        if width >= self.MIN_IMAGE_WIDTH and height >= self.MIN_IMAGE_HEIGHT:
            result = True
        if ratio < 1.0:
            result = False
        if ratio > 2.0:
            result = False

        return result

    def __repr__(self):
        name = ''

        if hasattr(self, 'subreddit_name'):
            name = self.subreddit_name
        else:
            name = 'Subreddit not initialized'

        return '<SubredditWallpaperCrawler: %s>' % name
