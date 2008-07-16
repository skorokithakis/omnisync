"""A file object class."""

class FileObject(object):
    """A file object that caches file attributes."""
    def __init__(self, transport, url, attributes=None):
        super(FileObject, self).__setattr__("_transport", transport)
        if not attributes:
            attributes = {}
        super(FileObject, self).__setattr__("_attr_dict", attributes)
        super(FileObject, self).__setattr__("url", url)

    def __getattr__(self, name):
        """Get the requested attribute from the cache, or fetch it if it doesn't exist.."""
        try:
            return self._attr_dict[name]
        except KeyError:
            if name == "isdir":
                self._attr_dict[name] = self._transport.isdir(self.url)
                return self._attr_dict[name]
            # See if we can getattr() for the attribute.
            elif name in self._transport.getattr_attributes:
                attrs = self._transport.getattr(self.url, name)
                self._attr_dict.update(attrs)
                return self._attr_dict[name]
            else:
                # Doing a listdir() is left as an exercise for the reader.
                raise

    def __eq__(self, other):
        """Test equality of two class instances."""
        if self.url == other.url:
            return True
        else:
            return False

    def __ne__(self, other):
        """Test inequality of two class instances."""
        if self.url != other.url:
            return True
        else:
            return False

    def __setattr__(self, name, value):
        """Set the requested attribute."""
        self._attr_dict[name] = value

    def __repr__(self):
        """Return a human-readable description of the object."""
        return self.url

    def __contains__(self, name):
        """Returns True if we have cached the attribute, False otherwise."""
        if name in self._attr_dict:
            return True
        else:
            return False

    @property
    def attribute_set(self):
        """Return a set of cached attributes."""
        return set(self._attr_dict)

    @property
    def attributes(self):
        """Return the cached attribute dict."""
        return self._attr_dict

    def populate_attributes(self, attr_list):
        """Retrieve a file's requested attributes and populate the instance's attributes
           with them."""
        for attribute in attr_list:
            if attribute not in self._attr_dict:
                assert attribute in self._transport.getattr_attributes, \
                       "Attribute %s not recoverable by getattr()" % attribute
                self._attr_dict.update(self._transport.getattr(self.url, [attribute]))
