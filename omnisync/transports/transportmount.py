"""Transport mounting module."""

class TransportMount(type):
    """The mount point class for transport modules."""
    def __init__(cls, name, bases, attrs):
        """Mount other transports modules."""
        if not hasattr(cls, "transports"):
            # If we are the main mount point, create a transport list.
            cls.transports = []
        else:
            # If we are a plugin implementation, append to the list.
            cls.transports.append(cls)

class TransportInterface:
    """Parent class for transport classes.
       Any subclass should try to implement as many of the following attributes as
       possible in listdir and stat:

       isdir - Whether the location is a directory. All the following are ignored
               if this is True (boolean).
       size  - The file size (long).
       mtime - Most recent content modification (seconds since the Epoch).
       md5   - The location's MD5 checksum (string).
       crc   - The location's CRC checksum (string).
       sha1  - The location's SHA1 checksum (string).
    """
    __metaclass__ = TransportMount
