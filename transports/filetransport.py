"""Plain file access module."""

from transports.transportmount import TransportInterface

import os
import urlparse
import time
import errno

try:
    OSERROR = WindowsError
except NameError:
    OSERROR = OSError

class FileTransport(TransportInterface):
    """Plain file access class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("file", "ftp")
    # listdir_attributes is a tuple that contains the file attributes that listdir()
    # supports.
    listdir_attributes = set()
    # Conversely, for getattr().
    # TODO: Get/set as many attributes as possible.
    getattr_attributes = set(("size", "mtime"))
    # List the attributes setattr() can set.
    setattr_attributes = set(("mtime", ))
    # Define attributes that can be used to decide whether a file has been changed
    # or not.
    evaluation_attributes = set(("size", "mtime"))
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

    def open(self, url, mode="rb"):
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
        try:
            os.remove(self.__get_filename(url))
        except OSERROR:
            return False
        else:
            return True

    def close(self):
        """Close the open file."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def mkdir(self, url):
        """Recursively make the given directories at the current URL."""
        current_path = ""
        for component in self.__get_filename(url).split("/"):
            current_path += component + "/"
            try:
                os.mkdir(current_path)
            except OSERROR, failure:
                if failure.errno != errno.EEXIST:
                    return False

        return True

    def listdir(self, url):
        """Retrieve a directory listing of the given location.

        Returns a list of (url, attribute_dict) tuples if the
        given URL is a directory, False otherwise.
        attribute_dict is a dictionary of {key: value} pairs for any applicable
        attributes from ("size", "mtime", "atime", "ctime", "isdir").
        """
        if not url.endswith("/"):
            url = url + "/"
        try:
            return [(url + x, {}) for x in os.listdir(self.__get_filename(url))]
        except OSERROR:
            return False

    def isdir(self, url):
        """Return True if the given URL is a directory, False if it is a file or
           does not exist."""
        return os.path.isdir(self.__get_filename(url))

    def getattr(self, url, attributes):
        """Retrieve (at least) the requested file attributes.

        Returns a dictionary whose keys are the items of attributes.
        """
        if set(attributes) - self.getattr_attributes:
            raise NotImplementedError, "Some requested attributes are not implemented."
        try:
            statinfo = os.stat(self.__get_filename(url))
        except OSERROR:
            return {"size": None, "mtime": None}
        return {"size": statinfo.st_size, "mtime": statinfo.st_mtime}

    def setattr(self, url, attributes):
        """Set a file's attributes if possible."""
        # We can only set mtime here.
        if "mtime" in attributes:
            os.utime(self.__get_filename(url), (time.time(), attributes["mtime"]))

    def exists(self, url):
        """Return True if a given path exists, False otherwise."""
        return os.path.exists(self.__get_filename(url))
