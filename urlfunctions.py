"""Implement URL helper functions"""

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
    """Append a slash to a URL, checking if it already has one."""
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

def url_join(source_base_url, source_full_url, destination_base_url):
    """Intelligently join the difference in path to a second URL. For example, if
       _source_base_url_ is "my_url/path", _source_full_url_ is "my_url/path/other/files" and
       _destination_base_url_ is "another_url/another_path" then the function should return
       "another_url/another_path/other/files".
    """
    assert source_full_url.startswith(source_base_url), "Full URL does not begin with base URL."
    url_difference = source_full_url[len(source_base_url):]
    url_difference = prepend_slash(url_difference, False)
    return append_slash(destination_base_url, True) + url_difference
