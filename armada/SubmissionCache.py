# ==============================================================================
# SubmissionCache.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from collections import deque


# ------------------------------------------------------------------------------
# Class
# ------------------------------------------------------------------------------

class SubmissionCache(object):
    """
    Stores and manages the most recently crawled submissions.
    """

    def __init__(self, size):
        """
        Create an empty submission cache.

        Arguments:
            size<int> -- Size of the cache.
        """
        self.cache = deque()
        self.max_size = size

    def has_item(self, item):
        """
        Checks if the item is in the cache.

        Arguments:
            item<string> -- Item to check.

        Returns:
            True if the item is in the cache, else False.
        """
        return item in self.cache

    def add(self, item):
        """
        Adds an item to the cache. If the item is already present, silently
        return.

        Arguments:
            item<string> -- Item to cache.
        """
        if self.has_item(item):
            return

        self.cache.append(item)

        if self.size() > self.max_size:
            self.cache.popleft()

    def size(self):
        """
        Returns the number of items in the cache.

        Returns:
            Number of items in cache.
        """
        return len(self.cache)
