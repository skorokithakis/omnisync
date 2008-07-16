"""S3 transport module."""

from omnisync.transportmount import TransportInterface
from omnisync.fileobject import FileObject
from omnisync import urlfunctions

import getpass
import time
import errno


class S3Transport(TransportInterface):
    """S3 transport class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("s3", )
    # Inform whether this transport's URLs use a hostname. The difference between http://something
    # and file://something is that in the former "something" is a hostname, but in the latter it's
    # a path.
    uses_hostname = True
    # listdir_attributes is a set that contains the file attributes that listdir()
    # supports.
    listdir_attributes = set(("size", ))
    # Conversely, for getattr().
    getattr_attributes = set()
    # List the attributes setattr() can set.
    setattr_attributes = set()
    # Define attributes that can be used to decide whether a file has been changed
    # or not.
    evaluation_attributes = set(("size", ))
    # The preferred buffer size for reads/writes.
    buffer_size = 2**15

    def __init__(self):
        self._bucket = None
        self._connection = None

    def _get_filename(self, url):
        """Retrieve the local filename from a given URL."""
        url = urlfunctions.append_slash(url, False)
        split_url = urlfunctions.url_split(url, uses_hostname=self.uses_hostname)
        return urlfunctions.prepend_slash(split_url.path, False)

    # Transports should also implement the following methods:
    def add_options(self):
        """Return the desired command-line plugin options.

           Returns a tuple of ((args), {kwargs}) items for optparse's add_option().
        """
        return ()

    def connect(self, url):
        """Initiate a connection to the remote host."""
        url = urlfunctions.url_split(url)
        if not url.username:
            print "S3: Please enter your AWS access key:",
            url.username = raw_input()
        if not url.password:
            url.password = getpass.getpass("S3: Please enter your AWS secret key:")
        global S3Connection, Key
        try:
            # We import boto here so the program doesn't crash if the library is not installed.
            from boto.s3.connection import S3Connection
            from boto.s3.key import Key
        except ImportError:
            print "S3: You will need to install the boto library to have s3 support."
            raise
        self._connection = S3Connection(url.username, url.password)
        try:
            self._bucket = self._connection.get_bucket(url.hostname)
        except boto.exception.S3ResponseError, failure:
            if failure.status == 404:
                self._bucket = self._connection.create_bucket(url.hostname)
            else:
                print "S3: Unspecified failure while connecting to the S3 bucket, aborting."

    def disconnect(self):
        """Do nothing, S3 doesn't require anything."""

    def open(self, url, mode="r"):
        """Open a file in _mode_ to prepare for I/O.

           Raises IOError if anything goes wrong.
        """
        self._file_handle = Key(self._bucket, self._get_filename(url))
        self._file_handle.open(mode.replace("b", ""))

    def read(self, size):
        """Read _size_ bytes from the open file."""
        return self._file_handle.read(size)

    #def write(self, data):
    #    """No writes yet for s3 :(."""
    #    self._file_handle.write(data)

    def remove(self, url):
        """Remove the specified file."""
        self._bucket.remove(self._get_filename(url))

    def rmdir(self, url):
        """Remove the specified directory non-recursively."""
        return True

    def close(self):
        """Close the open file."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

    def mkdir(self, url):
        """Where we're going, we don't *need* directories."""

    def listdir(self, url):
        """Retrieve a directory listing of the given location.

        Returns a list of (url, attribute_dict) tuples if the given URL is a directory,
        False otherwise. URLs should be absolute, including protocol, etc.
        attribute_dict is a dictionary of {key: value} pairs for any applicable
        attributes from ("size", "mtime", "atime", "ctime", "isdir").
        """
        url = urlfunctions.append_slash(url, True)
        url = urlfunctions.url_split(url)
        path = urlfunctions.prepend_slash(url.path, False)
        dir_list = self._bucket.list(prefix=path, delimiter="/")
        file_list = []
        for item in dir_list:
            # Prepend a slash by convention.
            url.path = "/" + item.name
            # list() returns directories ending with a slash.
            file_obj = FileObject(self, urlfunctions.url_join(url),
                                        {"isdir": item.name.endswith("/")})
            if not file_obj.isdir:
                file_obj.size = item.size
            else:
                file_obj.size = 0
            file_list.append(file_obj)
        return file_list

    def isdir(self, url):
        """Return True if the given URL is a directory, False if it is a file or
           does not exist."""
        return self.listdir(url) != []

    def getattr(self, url, attributes):
        """Do nothing."""
        # TODO: Retrieve ACL.

    def setattr(self, url, attributes):
        """Do nothing."""
        # TODO: Set ACL.

    def exists(self, url):
        """Return True if a given path exists, False otherwise."""
        filename = self._get_filename(url)
        # If we're looking for the root, return True.
        if filename == "":
            return True
        return Key(self._bucket, filename).exists()
