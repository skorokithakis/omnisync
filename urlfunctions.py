"""Implement URL helper functions"""

import re

URL_RE_HOSTNAME = re.compile("""^(?:(?P<scheme>\w+)://|)
                                 (?P<netloc>(?:(?P<username>.*?)(?::(?P<password>.*?)|)@|)
                                 (?P<hostname>[^@/]*?)(?::(?P<port>\d+)|))
                                 (?:(?P<path>/(?:.*?/|))
                                 /?(?P<file>[^/]*?|)|)
                                 (?:\;(?P<params>.*?)|)
                                 (?:\?(?P<query>.*?)|)
                                 (?:\#(?P<anchor>.*?)|)$""", re.VERBOSE)

URL_RE_PLAIN    = re.compile("""^(?:(?P<scheme>\w+)://|)
                                 (?:(?P<path>(?:.*?/|))
                                 /?(?P<file>[^/]*?|)|)
                                 (?:\;(?P<params>.*?)|)
                                 (?:\?(?P<query>.*?)|)
                                 (?:\#(?P<anchor>.*?)|)$""", re.VERBOSE)


class URLSplitResult(object):
    """Implement the result of url_split."""
    def __init__(self, match):
        # Call the superclass's __setattr__ to create the dictionary.
        super(URLSplitResult, self).__setattr__("_attr_dict", match)

    def __getattr__(self, name):
        """Get the requested attribute."""
        try:
            return self._attr_dict[name]
        except KeyError:
            return ""

    def __setattr__(self, name, value):
        """Set the requested attribute."""
        self._attr_dict[name] = value

    def get_dict(self):
        """Return a dictionary of only the attributes that have values set."""
        return dict((x[0], x[1]) for x in self._attr_dict.items() if x[1])

    def __repr__(self):
        """Return the dictionary representation of the class."""
        return repr(dict((x[0], x[1]) for x in self._attr_dict.items() if x[1]))


def url_split(url, uses_hostname=True, split_filename=False):
    """Split the URL into its components.

       uses_hostname defines whether the protocol uses a hostname or just a path (for
       "file://relative/directory"-style URLs) or not. split_filename defines whether the
       filename will be split off in an attribute or whether it will be part of the path
    """
    # urlparse.urlparse() is a bit deficient for our needs.
    try:
        if uses_hostname:
            match = URL_RE_HOSTNAME.match(url).groupdict()
        else:
            match = URL_RE_PLAIN.match(url).groupdict()
    except AttributeError:
        raise AttributeError, "Invalid URL."
    for key, item in match.items():
        if item is None:
            if key == "port":
                # We should leave port as None if it's not defined.
                match[key] = "0"
            else:
                match[key] = ""
    if uses_hostname:
        match["port"] = int(match["port"])
    if not split_filename:
        match["path"] = match["path"] + match["file"]
        match["file"] = ""

    return URLSplitResult(match)

def url_join(url):
    """Join a URLSplitResult class into a full URL. url_join(url_split(url)) returns _url_, with
       (valid) trailing slashes."""
    constructed_url = []
    if url.scheme:
        constructed_url.append(url.scheme + "://")
    constructed_url.append(url.username)
    if url.password:
        constructed_url.append(":" + url.password)
    if url.username or url.password:
        constructed_url.append("@")
    constructed_url.append(url.hostname)
    if url.port:
        constructed_url.append(":%s" % url.port)
    constructed_url.append(url.path)
    # If we have a file part and there is a hostname, make sure the path ends with a slash.
    if url.file and url.hostname and not url.path.endswith("/"):
        constructed_url.append("/")
    constructed_url.append(url.file)
    if url.params:
        constructed_url.append(";" + url.params)
    if url.query:
        constructed_url.append("?" + url.query)
    if url.anchor:
        constructed_url.append("#" + url.anchor)

    return "".join(constructed_url)

def append_slash(url, append=True):
    """Append a slash to a URL, checking if it already has one."""
    if url.endswith("/"):
        if append:
            return url
        else:
            return url[:-1]
    else:
        if append:
            return url + "/"
        else:
            return url

def prepend_slash(url, prepend=True):
    """Prepend a slash to a URL fragment, checking if it already has one."""
    if url.startswith("/"):
        if prepend:
            return url
        else:
            return url[1:]
    else:
        if prepend:
            return "/" + url
        else:
            return url

def url_splice(source_base_url, source_full_url, destination_base_url):
    """Intelligently join the difference in path to a second URL. For example, if
       _source_base_url_ is "my_url/path", _source_full_url_ is "my_url/path/other/files" and
       _destination_base_url_ is "another_url/another_path" then the function should return
       "another_url/another_path/other/files". The destination's query/parameters/anchor are left
       untouched.
    """
    source_base_url = url_split(source_base_url)
    source_full_url = url_split(source_full_url)
    destination_base_url = url_split(destination_base_url)
    assert source_full_url.path.startswith(source_base_url.path), \
           "Full URL does not begin with base URL."
    url_difference = source_full_url.path[len(source_base_url.path):]
    url_difference = prepend_slash(url_difference, False)
    destination_base_url.path = append_slash(destination_base_url.path, True) + url_difference
    return url_join(destination_base_url)

def normalise_url(url):
    """Normalise a URL from its shortcut to its proper form."""
    # Replace all backslashes with forward slashes.
    url = url.replace("\\", "/")

    # Prepend file:// to the URL if it lacks a protocol.
    split_url = url_split(url)
    if split_url.scheme == "":
        url = "file://" + url
    return url
