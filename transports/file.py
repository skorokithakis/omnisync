"""Plain file access module."""

from transports.transportmount import TransportInterface

class File(TransportInterface):
    """Plain file access class."""
    # Transports should have the protocols attribute to specify the protocol(s)
    # they can handle.
    protocols = ("file", )

    def connect(self, url):
        """This method does nothing, since we don't need to connect to the
           filesystem."""

    def disconnect(self):
        """This method does nothing, since we don't need to disconnect from the
           filesystem."""

    def open(self, url):
        """Open a file to prepare for reading."""

    def read(self, size):
        """Read _size_ bytes from the open file."""

    def write(self, data):
        """Write _data_ to the open file."""
        pass
    def delete(self, url):
        """Delete the specified file."""

    def close(self):
        """Close the open file."""

    def get_directory_list(self, directory):
        """Retrieve a directory list."""
