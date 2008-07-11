"""Virtual filesystem access module."""

from transports.transportmount import TransportInterface

import pickle
import urlfunctions

from fileobject import FileObject

class VirtualTransport(TransportInterface):
    """Virtual filesystem access class."""
    # Transports should declare the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("virtual", )
    # Inform whether this transport's URLs use a hostname. The difference between http://something
    # and file://something is that in the former "something" is a hostname, but in the latter it's
    # a path.
    uses_hostname = True
    # listdir_attributes is a tuple that contains the file attributes that listdir()
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
    def connect(self, url):
        """Unpickle the filesystem dictionary."""
        self._storage = urlfunctions.url_split(url).hostname
        try:
            pickled_file = open(self._storage, "rb")
        except IOError:
            return
        self._filesystem = pickle.load(pickled_file)
        pickled_file.close()

    def disconnect(self):
        """Pickle the filesystem to a file for persistence."""
        pickled_file = open(self._storage, "wb")
        pickle.dump(self._filesystem, pickled_file)
        pickled_file.close()

    def open(self, url, mode="rb"):
        """Open a file in _mode_ to prepare for I/O.

           Raises IOError if anything goes wrong.
        """
        self._file_handle = self._get_filename(url)
        if mode.startswith("r"):
            self._bytes_read = 0
        else:
            self._filesystem[self._file_handle] = {"size": 0}

    def read(self, size):
        """Read _size_ bytes from the open file."""
        if self._bytes_read + size < self._filesystem[self._file_handle]["size"]:
            self._bytes_read += size
            return " " * size
        else:
            bytes_read = self._bytes_read
            self._bytes_read = self._filesystem[self._file_handle]["size"]
            return " " * (self._filesystem[self._file_handle]["size"] - bytes_read)

    def write(self, data):
        """Write _data_ to the open file."""
        self._filesystem[self._file_handle]["size"] += len(data)

    def remove(self, url):
        """Remove the specified file/directory."""
        try:
            del self._filesystem[self._get_filename(url)]
        except KeyError:
            return False
        else:
            return True

    def close(self):
        """Close the open file."""
        self._file_handle = None

    def mkdir(self, url):
        """Do nothing, we don't need to make directories."""
        pass

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
        # If a file path starts with the directory we're looking for, there's obviously a directory
        # with that name.
        url = urlfunctions.append_slash(self._get_filename(url))
        for key in self._filesystem:
            if key.startswith(url):
                return True

    def getattr(self, url, attributes):
        """Retrieve as many file attributes as we can, at the very *least* the requested ones.

        Returns a dictionary whose keys are the values of the attributes.
        """
        try:
            return self._filesystem[self._get_filename(url)]
        except KeyError:
            return {"size": None}

    def setattr(self, url, attributes):
        """Do nothing."""

    def exists(self, url):
        """Return True if a given path exists, False otherwise."""
        if self._get_filename(url) in self._filesystem:
            return True
        for key in self._filesystem:
            if key.startswith(self._get_filename(url)):
                return True
        return False
