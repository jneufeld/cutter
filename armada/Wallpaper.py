# ==============================================================================
# Wallpaper.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import hashlib
from PIL import Image
import re
import StringIO
import urllib2


# ------------------------------------------------------------------------------
# Class
# ------------------------------------------------------------------------------

class Wallpaper(object):
    """
    A wallpaper, its thumbnail, and image metadata.
    """

    def __init__(self, image_url):
        """
        Creates a wallpaper from the given image URL. Throws an exception if the
        image data could not be extracted, or the object could not otherwise be
        created.

        Arguments:
            image_url<string> -- Absolute URL to image.
        """
        self.NAME_LENGTH = 10
        self.supported_extensions = ['jpg', 'png']

        self.url = image_url

        self.image = None
        self.image_width = 0
        self.image_height = 0
        self.image_format = None
        self.image_name = None

        self.thumbnail_width = 450
        self.thumbnail_height = 300
        self.thumbnail = None

        self.create_image()
        self.create_thumbnail()

    def create_image(self):
        """
        Creates the full image and sets its metadata.
        """
        self.get_image()
        self.set_image_size()
        self.set_image_format()
        self.set_image_name()

    def get_image(self, image_url=None, recurse=True):
        """
        Find and store the image blob.

        NOTE: If recurse is set to True and a poor URL is provided, it is
        possible to enter an infinite recursion. Please be careful with the
        recurse option.

        Arguments:
            image_url<string> -- Optional URL to try getting an image from.
            recurse<boolean>  -- If true, potentially look recursively at pages
                                 until an image is found.
        """
        url = self.url if not image_url else image_url

        extension = url[-3:]

        if extension in self.supported_extensions:
            self.image = urllib2.urlopen(url).read()
        elif recurse:
            hopeful_url = self.find_image_url(url)
            self.get_image(hopeful_url, False)

        if not self.image:
            raise Exception('Unable to create wallpaper image from URL.')

    def create_thumbnail(self):
        """
        Creates the thumbnail image and sets its metadata properties.
        """
        self.make_thumbnail()

    def make_thumbnail(self):
        """
        Create a thumbnail image from the full sized image.
        """
        size = (self.thumbnail_width, self.thumbnail_height)
        image_data = self.open_image(self.image)
        image_data.thumbnail(size, Image.ANTIALIAS)

        out_buffer = StringIO.StringIO()
        image_data.save(out_buffer, image_data.format)
        self.thumbnail = out_buffer.buflist[0]

    def open_image(self, image_blob):
        """
        Opens the Image file open for the given blob.

        Arguments:
            image_blob<string> -- Image blob.

        Returns:
            Opened Image file for the blob.
        """
        data_buffer = StringIO.StringIO()
        data_buffer.write(image_blob)
        data_buffer.seek(0)
        image_data = Image.open(data_buffer)

        return image_data

    def set_image_format(self):
        """
        Sets the image format.
        """
        image_data = self.open_image(self.image)
        self.image_format = image_data.format

    def set_image_name(self):
        """
        Creates a unique name for this image based on its source URL.
        """
        extension = '.jpg' if self.image_format == 'JPEG' else '.png'
        name = hashlib.md5(self.url).hexdigest()[:self.NAME_LENGTH]
        name += extension
        self.image_name = name

    def set_image_size(self):
        """
        Sets the dimensions of the full image.
        """
        image_data = self.open_image(self.image)
        self.image_width = image_data.size[0]
        self.image_height = image_data.size[1]

    def find_image_url(self, url):
        """
        Look through the source on the given page and try to find an image URL.

        Arguments:
            url<string> -- URL of an HTML page.

        Returns:
            An image URL if found, else None.
        """
        result = None

        if 'imgur.com' in url:
            result = self.get_imgur_image_url(url)

        return result

    def get_imgur_image_url(self, url):
        """
        Look through an imgur page and try to find an image URL.

        Arguments:
            url<string> -- URL of imgur HTML page.

        Returns:
            The URL of an image if found, else None.
        """
        result = None

        page_source = urllib2.urlopen(url).read()
        image_re = '(?P<link>i\.imgur\.com/\w+\.\w+)"'
        matches = re.search(image_re, page_source)
        image_url = 'http://' + matches.group('link')

        return result
