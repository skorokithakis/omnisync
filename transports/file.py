"""Plain file access module."""

from transports.transportmount import TransportInterface

import os
import urlparse
import time

class File(TransportInterface):
    """Plain file access class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("file", "ftp")
    # listdir_attributes is a tuple that contains the file attributes that listdir()
    # supports.
    listdir_attributes = set()
    # Conversely, for stat().
    stat_attributes = set(("size", "mtime", "atime", "ctime"))
    # The preferred buffer size for reads/writes.
    buffer_size = 2**15

    def __init__(self):
        self.file_handle = None

    def __get_filename(self, url):
        """Retrieve the local filename from a given URL."""
        split_url = urlparse.urlsplit(url)
        return split_url[1] + split_url[2]

    # Transports should also implement the following methods:
    def connect(self, url):
        """This method does nothing, since we don't need to connect to the
           filesystem."""

    def disconnect(self):
        """This method does nothing, since we don't need to disconnect from the
           filesystem."""

    def open(self, url, mode):
        """Open a file in _mode_ to prepare for reading.

           Raises IOError if anything goes wrong.
        """
        if self.file_handle:
            raise IOError, "Another file is already open."
        self.file_handle = open(self.__get_filename(url), mode)

    def read(self, size):
        """Read _size_ bytes from the open file."""
        return self.file_handle.read(size)

    def write(self, data):
        """Write _data_ to the open file."""
        self.file_handle.write(data)

    def remove(self, url):
        """Remove the specified file/directory."""
        os.remove(self.__get_filename(url))

    def close(self):
        """Close the open file."""
        self.file_handle.close()

    def mkdir(self, url):
        """Make a directory at the current URL."""
        os.mkdir(self.__get_filename(url))

    def listdir(self, url):
        """Retrieve a directory listing of the given location.

        Returns a list of (filename, attribute_dict) tuples if the
        given URL is a directory, False otherwise.
        attribute_dict is a dictionary of {key: value} pairs for any applicable
        attributes from ("size", "mtime", "atime", "ctime", "isdir").
        """
        try:
            return [(x, {}) for x in os.listdir(self.__get_filename(url))]
        except (OSError, WindowsError):
            return False

    def isdir(self, url):
        """Return True if the given URL is a directory, False if it is a file or
           does not exist."""
        return os.path.isdir(self.__get_filename(url))

    def stat(self, url):
        """Retrieve various file/directory attributes.

        Returns a dictionary whose keys are the items of stat_attributes.
        """
        try:
            statinfo = os.stat(self.__get_filename(url))
        except (OSError, WindowsError):
            return {"size": None, "mtime": None}
        return {"size": statinfo.st_size, "mtime": statinfo.st_mtime}

    def exists(self, url):
        """Return true if a given path exists."""
        return os.path.exists(self.__get_filename(url))

    def setattr(self, url, attributes):
        """Set a file's attributes if possible."""
        # We can only set mtime here.
        if "mtime" in attributes:
            os.utime(self.__get_filename(url), (time.time(), attributes["mtime"]))
