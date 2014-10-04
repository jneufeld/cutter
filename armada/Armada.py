# ==============================================================================
# Armada.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from DebugLogging import debug_logging
from time import sleep


# ------------------------------------------------------------------------------
# Class
# ------------------------------------------------------------------------------

class Armada(object):
    """
    Manages a fleet of crawlers.
    """

    @debug_logging
    def __init__(self, pause=30):
        """
        Creates a crawler manager.

        Arguments:
            pause<int> -- Wait time between crawls in seconds.
        """
        self.crawlers = []
        self.crawl_wait = pause

    @debug_logging
    def run(self):
        """
        Begins indefinite crawling, sequentially calling each crawler, then
        sleeps the pause time before starting over.
        """
        while True:
            for crawler in self.crawlers:
                crawler.crawl()

            sleep(self.crawl_wait)

    @debug_logging
    def add_crawler(self, crawler):
        """
        Adds a crawler to the fleet.
        """
        self.crawlers.append(crawler)

    def __repr__(self):
        return '<Armada>'
