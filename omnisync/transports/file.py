"""Plain file access module."""

from omnisync.transportmount import TransportInterface
from omnisync.fileobject import FileObject
from omnisync import urlfunctions

import platform
import os
import time
import errno

if platform.system() == "Windows":
    OSERROR = WindowsError
else:
    OSERROR = OSError


class FileTransport(TransportInterface):
    """Plain file access class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("file", )
    # Inform whether this transport's URLs use a hostname. The difference between http://something
    # and file://something is that in the former "something" is a hostname, but in the latter it's
    # a path.
    uses_hostname = False
    # listdir_attributes is a set that contains the file attributes that listdir()
    # supports.
    listdir_attributes = set()
    # Conversely, for getattr().
    getattr_attributes = set(("size", "mtime", "atime", "perms", "owner", "group"))
    # List the attributes setattr() can set.
    if platform.system() == "Windows":
        setattr_attributes = set(("mtime", "atime", "perms"))
    else:
        setattr_attributes = set(("mtime", "atime", "perms", "owner", "group"))
    # Define attributes that can be used to decide whether a file has been changed
    # or not.
    evaluation_attributes = set(("size", "mtime"))
    # The preferred buffer size for reads/writes.
    buffer_size = 2**15

    def __init__(self):
        self._file_handle = None

    def _get_filename(self, url):
        """Retrieve the local filename from a given URL."""
        split_url = urlfunctions.url_split(url, uses_hostname=self.uses_hostname)
        return split_url.path

    # Transports should also implement the following methods:
    def add_options(self):
        """Return the desired command-line plugin options.

           Returns a tuple of ((args), {kwargs}) items for optparse's add_option().
        """
        return ()

    def connect(self, url):
        """This method does nothing, since we don't need to connect to the
           filesystem."""

    def disconnect(self):
        """This method does nothing, since we don't need to disconnect from the
           filesystem."""

    def open(self, url, mode="rb"):
        """Open a file in _mode_ to prepare for I/O.

           Raises IOError if anything goes wrong.
        """
        if self._file_handle:
            raise IOError, "Another file is already open."
        self._file_handle = open(self._get_filename(url), mode)

    def read(self, size):
        """Read _size_ bytes from the open file."""
        return self._file_handle.read(size)

    def write(self, data):
        """Write _data_ to the open file."""
        self._file_handle.write(data)

    def remove(self, url):
        """Remove the specified file."""
        try:
            os.remove(self._get_filename(url))
        except OSERROR:
            return False
        else:
            return True

    def rmdir(self, url):
        """Remove the specified directory non-recursively."""
        try:
            os.rmdir(self._get_filename(url))
        except OSERROR:
            return False
        else:
            return True

    def close(self):
        """Close the open file."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

    def mkdir(self, url):
        """Recursively make the given directories at the current URL."""
        # Recursion is not needed for anything but the first directory, so we need to be able to
        # do it.
        current_path = ""
        error = False
        for component in self._get_filename(url).split("/"):
            current_path += component + "/"
            try:
                os.mkdir(current_path)
            except OSERROR, failure:
                if failure.errno != errno.EEXIST:
                    error = True
            else:
                error = False

        return error

    def listdir(self, url):
        """Retrieve a directory listing of the given location.

        Returns a list of (url, attribute_dict) tuples if the given URL is a directory,
        False otherwise. URLs should be absolute, including protocol, etc.
        attribute_dict is a dictionary of {key: value} pairs for any applicable
        attributes from ("size", "mtime", "atime", "ctime", "isdir").
        """
        if not url.endswith("/"):
            url = url + "/"
        try:
            return [FileObject(self, url + x) for x in os.listdir(self._get_filename(url))]
        except OSERROR:
            return False

    def isdir(self, url):
        """Return True if the given URL is a directory, False if it is a file or
           does not exist."""
        return os.path.isdir(self._get_filename(url))

    def getattr(self, url, attributes):
        """Retrieve as many file attributes as we can, at the very *least* the requested ones.

        Returns a dictionary of {"attribute": "value"}, or {"attribute": None} if the file does
        not exist.
        """
        if set(attributes) - self.getattr_attributes:
            raise NotImplementedError, "Some requested attributes are not implemented."
        try:
            statinfo = os.stat(self._get_filename(url))
        except OSERROR:
            return dict([(x, None) for x in self.getattr_attributes])
        # Turn times to ints because checks fail sometimes due to rounding errors.
        return {"size": statinfo.st_size,
                "mtime": int(statinfo.st_mtime),
                "atime": int(statinfo.st_atime),
                "perms": statinfo.st_mode,
                "owner": statinfo.st_uid,
                "group": statinfo.st_gid,
                }

    def setattr(self, url, attributes):
        """Set a file's attributes if possible."""
        filename = self._get_filename(url)
        if "atime" in attributes or "mtime" in attributes:
            atime = attributes.get("atime", time.time())
            mtime = attributes.get("mtime", time.time())
            try:
                os.utime(filename, (atime, mtime))
            except OSERROR:
                print "FILE: Permission denied, could not set atime/mtime on %s." % url
        if "perms" in attributes:
            try:
                os.chmod(filename, attributes["perms"])
            except OSERROR:
                print "FILE: Permission denied, could not set perms on %s." % url
        if platform.system() != "Windows" and ("owner" in attributes or "group" in attributes):
            try:
                os.chown(filename, attributes.get("owner", -1), attributes.get("group", -1))
            except OSERROR:
                print "FILE: Permission denied, could not set uid/gid on %s." % url

    def exists(self, url):
        """Return True if a given path exists, False otherwise."""
        return os.path.exists(self._get_filename(url))
