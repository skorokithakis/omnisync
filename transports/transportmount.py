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
    """Parent class for transport classes."""
    __metaclass__ = TransportMount
