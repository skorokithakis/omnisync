"""SFTP transport module."""

from omnisync.transportmount import TransportInterface
from omnisync.fileobject import FileObject
from omnisync import urlfunctions

import getpass
import time
import errno


class SFTPTransport(TransportInterface):
    """SFTP transport class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("sftp", )
    # Inform whether this transport's URLs use a hostname. The difference between http://something
    # and file://something is that in the former "something" is a hostname, but in the latter it's
    # a path.
    uses_hostname = True
    # listdir_attributes is a set that contains the file attributes that listdir()
    # supports.
    listdir_attributes = set(("size", "mtime", "atime", "perms", "owner", "group"))
    # Conversely, for getattr().
    getattr_attributes = set(("size", "mtime", "atime", "perms", "owner", "group"))
    # List the attributes setattr() can set.
    setattr_attributes = set(("mtime", "atime", "perms", "owner", "group"))
    # Define attributes that can be used to decide whether a file has been changed
    # or not.
    evaluation_attributes = set(("size", "mtime"))
    # The preferred buffer size for reads/writes.
    buffer_size = 2**15

    def __init__(self):
        self._file_handle = None
        self._connection = None
        self._transport = None

    def _get_filename(self, url):
        """Retrieve the local filename from a given URL."""
        split_url = urlfunctions.url_split(url, uses_hostname=self.uses_hostname)
        # paths are relative unless they start with two //
        path = split_url.path
        if len(path) > 1 and path.startswith("/"):
            path = path[1:]
        return path

    # Transports should also implement the following methods:
    def add_options(self):
        """Return the desired command-line plugin options.

           Returns a tuple of ((args), {kwargs}) items for optparse's add_option().
        """
        return ()

    def connect(self, url, config):
        """Initiate a connection to the remote host."""
        options = config.full_options
        
        # Make the import global.
        global paramiko
        try:
            # We import paramiko only when we need it because its import is really slow.
            import paramiko
        except ImportError:
            print "SFTP: You will need to install the paramiko library to have sftp support."
            raise
        url = urlfunctions.url_split(url)
        if not url.port:
            url.port = 22
        self._transport = paramiko.Transport((url.hostname, url.port))
        
        username = url.username
        if not url.username:
            if hasattr(options, "username"):
                username = options.username
            else:
                url.username = getpass.getuser()
        
        password = url.password
        if not url.password:
            if hasattr(options, "password"):
                password = options.password
            else:
                password = getpass.getpass(
                    "SFTP: Please enter the password for %s@%s:" % (url.username, url.hostname)
                )
        self._transport.connect(username=username, password=password)
        self._connection = paramiko.SFTPClient.from_transport(self._transport)

    def disconnect(self):
        """Disconnect from the remote server."""
        self._transport.close()

    def open(self, url, mode="rb"):
        """Open a file in _mode_ to prepare for I/O.

           Raises IOError if anything goes wrong.
        """
        if self._file_handle:
            raise IOError, "Another file is already open."
        self._file_handle = self._connection.open(self._get_filename(url), mode)

    def read(self, size):
        """Read _size_ bytes from the open file."""
        return self._file_handle.read(size)

    def write(self, data):
        """Write _data_ to the open file."""
        self._file_handle.write(data)

    def remove(self, url):
        """Remove the specified file."""
        try:
            self._connection.remove(self._get_filename(url))
        except IOError:
            return False
        else:
            return True

    def rmdir(self, url):
        """Remove the specified directory non-recursively."""
        try:
            self._connection.rmdir(self._get_filename(url))
        except IOError:
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
                self._connection.mkdir(current_path)
            except IOError, failure:
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
        url = urlfunctions.append_slash(url, True)
        try:
            dir_list = self._connection.listdir_attr(self._get_filename(url))
        except IOError:
            return False
        file_list = []
        for item in dir_list:
            file_list.append(FileObject(self, url + item.filename,
                {"size": item.st_size,
                 "mtime": item.st_mtime,
                 "atime": item.st_atime,
                 "perms": item.st_mode,
                 "owner": item.st_uid,
                 "group": item.st_gid,
                }))
        return file_list

    def isdir(self, url):
        """Return True if the given URL is a directory, False if it is a file or
           does not exist."""
        try:
            # paramiko doesn't allow you to check any other way.
            self._connection.listdir(self._get_filename(url))
        except IOError, failure:
            if failure.errno == errno.ENOENT:
                return False
            else:
                raise
        else:
            return True

    def getattr(self, url, attributes):
        """Retrieve as many file attributes as we can, at the very *least* the requested ones.

        Returns a dictionary of {"attribute": "value"}, or {"attribute": None} if the file does
        not exist.
        """
        if set(attributes) - self.getattr_attributes:
            raise NotImplementedError, "Some requested attributes are not implemented."
        try:
            statinfo = self._connection.stat(self._get_filename(url))
        except IOError:
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
                self._connection.utime(filename, (atime, mtime))
            except IOError:
                print "SFTP: Permission denied, could not set atime/mtime."
        if "perms" in attributes:
            try:
                self._connection.chmod(filename, attributes["perms"])
            except IOError:
                print "SFTP: Permission denied, could not set perms."
        if "owner" in attributes or "group" in attributes:
            # If we're missing one, get it.
            if not "owner" in attributes or not "group" in attributes:
                stat = self._connection.stat(filename)
                owner = attributes.get("owner", stat.st_uid)
                group = attributes.get("group", stat.st_gid)
            else:
                owner = attributes["owner"]
                group = attributes["group"]
            try:
                self._connection.chown(filename, owner, group)
            except IOError:
                print "SFTP: Permission denied, could not set uid/gid."

    def exists(self, url):
        """Return True if a given path exists, False otherwise."""
        try:
            self._connection.stat(self._get_filename(url))
        except IOError:
            return False
        else:
            return True
