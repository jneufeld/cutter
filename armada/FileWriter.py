# ==============================================================================
# FileWriter.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import os


# ------------------------------------------------------------------------------
# Class
# ------------------------------------------------------------------------------

class FileWriter(object):
    """
    Manages writing image files to the filesystem.
    """

    def __init__(self):
        """
        Creates a file writer.
        """
        pass

    def file_exists(self, path):
        """
        Checks if a file exists given the absolute path.

        Arguments:
            path<string> -- Absolute path including filename.

        Returns:
            True if the file exists, else False.
        """
        result = False

        try:
            result = os.path.isfile(path)
        except Exception as error:
            print 'Unable to check if file exists: %s. Details: %s' % (path,
                error)

        return result

    def write(self, content, path, name):
        """
        Write the content to the given file. Silently continues without writing
        if the file already exists.

        Arguments:
            content<string> -- Blob content to write to file.
            path<string>    -- Absolute filesystem path.
            name<string>    -- File name, including extension.

        Returns:
            True if the file was written, else False.
        """
        result = False

        if not self.file_exists(path + name):
            handler = open(path + name, 'w')
            handler.write(content)
            handler.close()
            result = True

        return result

    def unwrite(self, path, name):
        """
        Rolls back a write at the given path if the file exists. If the file
        does not exist, fails silently.

        Arguments:
            path<string> -- Absolute path including filename.
        """
        if self.file_exists(path + name):
            handler = os.remove(path + name)
