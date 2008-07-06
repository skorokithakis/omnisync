"""Plain file access module."""

from transports.transportmount import TransportInterface

import os
import urlparse

class File(TransportInterface):
    """Plain file access class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("file", )

    def __init__(self):
        """Initialise the class."""
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
        """Open a file in _mode_ to prepare for reading."""
        self.file_handle = open(url, mode)

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

        Returns a list of (filename, is_directory) tuples if the given URL is a
        directory, False otherwise
        """
        try:
            items = os.listdir(self.__get_filename(url))
        except (OSError, WindowsError):
            return False
        return [(item, os.path.isdir(item)) for item in items]

    def isdir(self, url):
        """Return True if the given URL is a directory, False if it is a file."""
        return os.path.isdir(self.__get_filename(url))

    def stat(self, url):
        """Retrieve various file/directory attributes."""

    def exists(self, url):
        """Return true if a given path exists."""
        return os.path.exists(self.__get_filename(url))
