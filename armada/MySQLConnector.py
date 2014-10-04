# ==============================================================================
# MySQLConnector.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import mysql.connector
from mysql.connector import errorcode, IntegrityError


# ------------------------------------------------------------------------------
# Class
# ------------------------------------------------------------------------------

class MySQLConnector(object):
    """
    Creates a database connection to a MySQL database.  

    For the sake of documentation, here is the Wallpapers table:

        CREATE TABLE IF NOT EXISTS Wallpapers (
            name VARCHAR(10),
            source VARCHAR(1024) NOT NULL,
            img_height INT NOT NULL,
            img_width INT NOT NULL,
            image_blob BLOB NOT NULL,
            PRIMARY KEY (name)
        );

    And the Keywords table:

        CREATE TABLE IF NOT EXISTS Keywords (
            word VARCHAR(32),
            name VARCHAR(10),
            PRIMARY KEY (word, name),
            FOREIGN KEY (name) REFERENCES Wallpapers(name)
        );
    """

    def __init__(self,
            database_name,
            username,
            password,
            wallpaper_table,
            keyword_table,
            host='127.0.0.1'):
        """
        Creates a connection to a MySQL database.

        Arguments:
            database_name<string>   -- Name of the database to use.
            username<string>        -- Username to connect with.
            password<string>        -- Password to connect with.
            wallpaper_table<string> -- Table to write wallpapers to.
            keyword_table<string>   -- Table to write keywords to.
            host<string>            -- Optional host address.
        """
        if not database_name:
            raise Exception('Database name must not be empty.')
        if not username:
            raise Exception('Database username name must not be empty.')
        if not password:
            raise Exception('Database password must not be empty.')
        if not wallpaper_table:
            raise Exception('Wallpaper table name must not be empty.')
        if not keyword_table:
            raise Exception('Keyword table name must not be empty.')
        if not host:
            raise Exception('Host name must not be empty.')

        self.db_name = database_name
        self.wallpaper_table = wallpaper_table
        self.keyword_table = keyword_table

        self.username = username
        self.password = password
        self.host = host

        self.connection = self.get_connection()

        if self.connection == None:
            raise Exception('Unable to connect to database.')

    def get_connection(self):
        """
        Creates connection to the database or swallows the exception and prints
        the error.

        Returns:
            Database connection if successful, otherwise returns None.
        """
        result = None

        try:
            result = mysql.connector.connect(user=self.username,
                password=self.password,
                database=self.db_name,
                host=self.host)
        except mysql.connector.Error as error:
            if error.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print 'Could not connect usering username=%s, password=%s' % \
                    (self.username, self.password)
            elif error.errno == errorcode.ER_BAD_DB_ERROR:
                print 'Database does not exist: %s' % self.db_name
            else:
                print error

        return result

    def store(self, image, name, keywords, source, size):
        """
        Stores the image and its metadata.

        Arguments:
            image<string>      -- Image to store, in blob form.
            name<string>       -- Hashed name of image.
            keywords<[string]> -- Keywords describing the image.
            source<string>     -- Absolute URL to the source of the image.
            size<(int, int)>   -- Contains width and height of image.
        """
        if not image:
            raise Exception('Cannot write empty image to DB.')
        if not name:
            raise Exception('Cannot write empty image name to DB.')
        if not keywords:
            raise Exception('Cannot write image to DB without keywords.')
        if not source:
            raise Exception('Cannot write image to DB without source URL.')
        if not size or len(size) != 2:
            raise Exception('Cannot write image to DB without size data.')

        cursor = self.connection.cursor()

        wrote = self.write_wallpaper(cursor,
            name,
            source,
            size[0],
            size[1],
            image)

        if wrote:
            self.write_keywords(cursor, name, keywords)

        self.connection.commit()
        cursor.close()

    def write_wallpaper(self, cursor, name, source, width, height, image):
        """
        Write the wallpaper to the wallpapers table. Return False if the add
        failed, otherwise return True.

        Arguments:
            cursor         -- Database cursor.
            name<string>   -- Hashed name of image.
            source<string> -- Absolute URL to the source of the image.
            width<int>     -- Pixel width of the image.
            height<int>    -- Pixel height of the image.
            image<string>  -- Image to store, in blob form.

        Returns:
            True if wallpaper was successfuly added.
        """
        result = False

        insert_line = 'INSERT INTO %s ' % self.wallpaper_table
        wallpaper_query = (insert_line + 'VALUES (%s, %s, %s, %s, %s)')
        wallpaper_args = (name, source, height, width, image)

        try:
            cursor.execute(wallpaper_query, wallpaper_args)
            result = True
        except IntegrityError as error:
            print 'Unable to add %s to Wallpapers, duplicate entry.' % name
        except Exception as error:
            print 'Unable to add %s to Wallpapers. Details: %s' % (name, error)

        return result

    def write_keywords(self, cursor, name, keywords): 
        """
        Write the keywords to the keyword table.

        Arguments:
            cursor           -- Database cursor.
            name<string>     -- Hashed name of image.
            keywords[string] -- Keywords for the wallpaper.
        """
        insert_line = 'INSERT INTO %s ' % self.keyword_table
        keyword_query = (insert_line + 'VALUES (%s, %s)')

        for keyword in keywords:
            try:
                keyword_args = (keyword, name)
                cursor.execute(keyword_query, keyword_args)
            except Exception as error:
                print 'Unable to add %s as keyword. Details: %s.' % (keyword,
                    error)

    def __repr__(self):
        name = ''

        if hasattr(self, 'db_name'):
            name = self.db_name
        else:
            name = 'DB name not yet initialized.'

        return '<MySQLConnector: %s>' % name
