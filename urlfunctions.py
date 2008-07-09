"""Implement URL helper functions"""

import re

URL_RE = re.compile("""^(?:(?P<scheme>\w+)://|)
                        (?P<netloc>(?:(?P<username>.*?)(?::(?P<password>.*?)|)@|)
                        (?P<hostname>[^/]*?)(?::(?P<port>\d+)|))
                        (?:(?P<path>/(?:.*?/|))
                        /?(?P<file>[^/]*?|)|)
                        (?:\;(?P<params>.*?)|)
                        (?:\?(?P<query>.*?)|)
                        (?:\#(?P<anchor>.*?)|)$""", re.VERBOSE)


class URLSplitResult:
    """Implement the result of url_split."""
    def __init__(self, match):
        self._attr_dict = match

    def __getattr__(self, attribute):
        """Get the requested attribute."""
        return self._attr_dict[attribute]

    def get_dict(self):
        """Return a dictionary of only the attributes that have values set."""
        return dict((x[0], x[1]) for x in self._attr_dict.items() if x[1])

    def __repr__(self):
        """Return the dictionary representation of the class."""
        return repr(dict((x[0], x[1]) for x in self._attr_dict.items() if x[1]))


def url_split(url, split_hostname=True, split_filename=False):
    """Split the URL into its components. urlparse.urlparse() is a bit deficient for our needs.
       split_hostname defines whether the hostname will be separate or prepended to the path
       (for "file://relative/directory"-style URLs) or not. split_filename defines whether the
       filename will be split off in an attribute or whether it will be part of the path"""
    try:
        match = URL_RE.match(url).groupdict()
    except AttributeError:
        raise AttributeError, "Invalid URL."
    for key, item in match.items():
        if item is None:
            if key == "port":
                # We should leave port as None if it's not defined.
                match[key] = "0"
            else:
                match[key] = ""
    match["port"] = int(match["port"])
    if not split_filename:
        match["path"] = match["path"] + match["file"]
        match["file"] = ""
    if not split_hostname:
        match["path"] = match["hostname"] + match["path"]
        match["hostname"] = ""

    return URLSplitResult(match)

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
       "another_url/another_path/other/files".
    """
    assert source_full_url.startswith(source_base_url), "Full URL does not begin with base URL."
    url_difference = source_full_url[len(source_base_url):]
    url_difference = prepend_slash(url_difference, False)
    return append_slash(destination_base_url, True) + url_difference
