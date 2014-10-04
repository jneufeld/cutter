# ==============================================================================
# Armada.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from time import sleep


# ------------------------------------------------------------------------------
# Class
# ------------------------------------------------------------------------------

class Armada(object):
    """
    Manages a fleet of crawlers.
    """

    def __init__(self, pause=900):
        """
        Creates a crawler manager.

        Arguments:
            pause<int> -- Wait time between crawls in seconds.
        """
        self.crawlers = []
        self.crawl_wait = pause

    def run(self):
        """
        Begins indefinite crawling, sequentially calling each crawler, then
        sleeps the pause time before starting over.
        """
        while True:
            for crawler in self.crawlers:
                crawler.crawl()

            sleep(self.crawl_wait)

    def add_crawler(self, crawler):
        """
        Adds a crawler to the fleet.
        """
        self.crawlers.append(crawler)

    def __repr__(self):
        return '<Armada>'
