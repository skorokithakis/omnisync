"""Virtual filesystem access module."""

from omnisync.transportmount import TransportInterface
from omnisync.fileobject import FileObject
from omnisync import urlfunctions

import pickle


class VirtualTransport(TransportInterface):
    """Virtual filesystem access class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("virtual", )
    # Inform whether this transport's URLs use a hostname. The difference between http://something
    # and file://something is that in the former "something" is a hostname, but in the latter it's
    # a path.
    uses_hostname = True
    # listdir_attributes is a set that contains the file attributes that listdir()
    # supports.
    listdir_attributes = set()
    # Conversely, for getattr().
    getattr_attributes = set(("size", ))
    # List the attributes setattr() can set.
    setattr_attributes = set()
    # Define attributes that can be used to decide whether a file has been changed
    # or not.
    evaluation_attributes = set(("size", ))
    # The preferred buffer size for reads/writes.
    buffer_size = 2**15

    def __init__(self):
        self._file_handle = None
        self._filesystem = {"/": None}
        self._storage = None
        self._bytes_read = None

    def _get_filename(self, url, remove_slash=True):
        """Retrieve the local filename from a given URL."""
        # Remove the trailing slash as a convention unless specified otherwise.
        if remove_slash:
            urlfunctions.append_slash(url, False)
        filename = urlfunctions.url_split(url).path
        if filename == "":
            filename = "/"
        return filename

    # Transports should also implement the following methods:
    def add_options(self):
        """Return the desired command-line plugin options.

           Returns a tuple of ((args), {kwargs}) items for optparse's add_option().
        """
        return ()

    def connect(self, url):
        """Unpickle the filesystem dictionary."""
        self._storage = urlfunctions.url_split(url).hostname
        # If the storage is in-memory only, don't do anything.
        if self._storage == "memory":
            return
        try:
            pickled_file = open(self._storage, "rb")
        except IOError:
            return
        self._filesystem = pickle.load(pickled_file)
        pickled_file.close()

    def disconnect(self):
        """Pickle the filesystem to a file for persistence."""
        # If the storage is in-memory only, don't do anything.
        if self._storage == "memory":
            return
        pickled_file = open(self._storage, "wb")
        pickle.dump(self._filesystem, pickled_file)
        pickled_file.close()

    def open(self, url, mode="rb"):
        """Open a file in _mode_ to prepare for I/O.

           Raises IOError if anything goes wrong.
        """
        filename = self._get_filename(url)
        if self._filesystem.get(filename, False) is None:
            raise IOError, "File is a directory."
        self._file_handle = filename
        if mode.startswith("r"):
            if filename not in self._filesystem:
                raise IOError, "File does not exist."
            self._bytes_read = 0
        else:
            self._filesystem[self._file_handle] = {"size": 0}

    def read(self, size):
        """Read _size_ bytes from the open file."""
        if self._file_handle is None:
            return IOError, "No file is open."
        if self._bytes_read + size < self._filesystem[self._file_handle]["size"]:
            self._bytes_read += size
            return " " * size
        else:
            bytes_read = self._bytes_read
            self._bytes_read = self._filesystem[self._file_handle]["size"]
            return " " * (self._filesystem[self._file_handle]["size"] - bytes_read)

    def write(self, data):
        """Write _data_ to the open file."""
        if self._file_handle is None:
            return IOError, "No file is open."
        self._filesystem[self._file_handle]["size"] += len(data)

    def close(self):
        """Close the open file."""
        self._file_handle = None

    def remove(self, url):
        """Remove the specified file."""
        filename = self._get_filename(url)
        if filename not in self._filesystem or self._filesystem[filename] is None:
            return False
        del self._filesystem[filename]
        return True

    def rmdir(self, url):
        """Remove the specified directory non-recursively."""
        filename = self._get_filename(url)
        if self._filesystem[filename] is not None:
            return False
        if self.listdir(url):
            return False
        else:
            del self._filesystem[filename]
            return True

    def mkdir(self, url):
        """Create a directory."""
        filename = self._get_filename(url)
        if filename not in self._filesystem:
            return IOError, "A directory with the specified name already exists."
        self._filesystem[filename] = None

    def listdir(self, url):
        """Retrieve a directory listing of the given location.

        Returns a list of (url, attribute_dict) tuples if the
        given URL is a directory, False otherwise.
        """
        # Add a slash so we don't have to remove it from the start of the subpaths.
        url = urlfunctions.append_slash(url)
        filename = self._get_filename(url, False)
        files = set()
        for key in self._filesystem:
            # Check the length to prevent returning the directory itself.
            if key.startswith(filename) and len(key) > len(filename):
                subpath = key[len(filename):]
                if "/" not in subpath:
                    # Add the subpath in the set as is, because there are no lower levels.
                    files.add(subpath)
                else:
                    files.add(subpath[:subpath.find("/")])
        return [FileObject(self, url + x,) for x in files]

    def isdir(self, url):
        """Return True if the given URL is a directory, False if it is a file or
           does not exist."""
        filename = self._get_filename(url)
        if filename not in self._filesystem:
            return False
        return self._filesystem[filename] is None

    def getattr(self, url, attributes):
        """Retrieve as many file attributes as we can, at the very *least* the requested ones.

        Returns a dictionary of {"attribute": "value"}, or {"attribute": None} if the file does
        not exist.
        """
        try:
            attrs = self._filesystem[self._get_filename(url)]
        except KeyError:
            return {"size": None}
        if attrs is None:
            # Directories have no attributes in our virtual FS.
            return {"size": None}
        else:
            return attrs

    def setattr(self, url, attributes):
        """Do nothing."""

    def exists(self, url):
        """Return True if a given path exists, False otherwise."""
        return self._get_filename(url) in self._filesystem
