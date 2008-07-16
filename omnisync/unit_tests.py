#!/usr/bin/env python
"""omnisync unit tests."""

import unittest
from omnisync import urlfunctions

class Tests(unittest.TestCase):
    """Various omnisync unit tests."""

    def test_append_slash(self):
        """Test append_slash."""
        tests = (
            (("file:///home/user/", True), "file:///home/user/"),
            (("file:///home/user/", False), "file:///home/user"),
            (("file:///home/user/", True), "file:///home/user/"),
            (("file:///home/user", False), "file:///home/user"),
        )
        for test, expected_output in tests:
            self.assertEqual(urlfunctions.append_slash(*test), expected_output)

    def test_prepend_slash(self):
        """Test append_slash."""
        tests = (
            (("/home/user/", True), "/home/user/"),
            (("/home/user/", False), "home/user/"),
            (("home/user/", True), "/home/user/"),
            (("home/user/", False), "home/user/"),
        )
        for test, expected_output in tests:
            self.assertEqual(urlfunctions.prepend_slash(*test), expected_output)

    def test_url_join(self):
        """Test url_join."""
        tests = (
            ("http://user:pass@myhost:80/some/path/file;things?myhost=hi#lala", True, True),
            ("http://user:pass@myhost:80/some/path/;things?myhost=hi#lala", True, True),
            ("http://user@myhost/file;things?myhost=hi#lala", True, True),
            ("http://myhost/;things?myhost=hi#lala", True, True),
            ("http://user:pass@myhost:80/?myhost=hi#lala", True, True),
            ("myhost/", True, True),
            ("user:pass@myhost:80/", True, True),
            ("user:pass@myhost/some#lala", True, True),
            ("http://myhost:80/;things?myhost=hi#lala", True, True),
            ("http://myhost/#lala", True, True),
            ("file://path", False, True),
            ("file://path/file", False, True),
            ("file:///path", False, True),
            ("file:///path/file", False, True),
            ("file:///path/file?something=else", False, True),
        )
        for test in tests:
            self.assertEqual(urlfunctions.url_join(urlfunctions.url_split(*test)), test[0])

    def test_url_split(self):
        """Test url_split."""
        tests = (
            (("http://user:pass@myhost:80/some/path/file;things?myhost=hi#lala", True, False),
             {"scheme": "http",
              "netloc": "user:pass@myhost:80",
              "username": "user",
              "password": "pass",
              "hostname": "myhost",
              "port": 80,
              "path": "/some/path/file",
              "file": "",
              "params": "things",
              "query": "myhost=hi",
              "anchor": "lala"}),
            (("http://myhost/some/path/file;things?myhost=hi#lala", True, False),
             {"scheme": "http",
              "netloc": "myhost",
              "username": "",
              "password": "",
              "hostname": "myhost",
              "port": 0,
              "path": "/some/path/file",
              "file": "",
              "params": "things",
              "query": "myhost=hi",
              "anchor": "lala"}),
            (("http://user@myhost/some/path/", True, False),
             {"scheme": "http",
              "netloc": "user@myhost",
              "username": "user",
              "password": "",
              "hostname": "myhost",
              "port": 0,
              "path": "/some/path/",
              "file": "",
              "params": "",
              "query": "",
              "anchor": ""}),
            (("http://myhost", True, False),
             {"scheme": "http",
              "netloc": "myhost",
              "username": "",
              "password": "",
              "hostname": "myhost",
              "port": 0,
              "path": "",
              "file": "",
              "params": "",
              "query": "",
              "anchor": ""}),
            (("file://some/directory", False, False),
             {"scheme": "file",
              "path": "some/directory",
              "file": "",
              "params": "",
              "query": "",
              "anchor": ""}),
            (("file://some/directory", True, True),
             {"scheme": "file",
              "netloc": "some",
              "username": "",
              "password": "",
              "hostname": "some",
              "port": 0,
              "path": "/",
              "file": "directory",
              "params": "",
              "query": "",
              "anchor": ""}),
            (("host", True, True),
             {"scheme": "",
              "netloc": "host",
              "username": "",
              "password": "",
              "hostname": "host",
              "port": 0,
              "path": "",
              "file": "",
              "params": "",
              "query": "",
              "anchor": ""}),
            (("http://user:pass@myhost:80/some/path/file;things?arg=hi#lala", True, True),
             {"scheme": "http",
              "netloc": "user:pass@myhost:80",
              "username": "user",
              "password": "pass",
              "hostname": "myhost",
              "port": 80,
              "path": "/some/path/",
              "file": "file",
              "params": "things",
              "query": "arg=hi",
              "anchor": "lala"}),
            (("http://myhost:80/some/path/file;things?arg=hi#lala", True, False),
             {"scheme": "http",
              "netloc": "myhost:80",
              "username": "",
              "password": "",
              "hostname": "myhost",
              "port": 80,
              "path": "/some/path/file",
              "file": "",
              "params": "things",
              "query": "arg=hi",
              "anchor": "lala"}),
            (("http://user:pass@myhost:80/some/path/file#lala", True, False),
             {"scheme": "http",
              "netloc": "user:pass@myhost:80",
              "username": "user",
              "password": "pass",
              "hostname": "myhost",
              "port": 80,
              "path": "/some/path/file",
              "file": "",
              "params": "",
              "query": "",
              "anchor": "lala"}),
            (("file://I:/some/path/file", False, True),
             {"scheme": "file",
              "path": "I:/some/path/",
              "file": "file",
              "params": "",
              "query": "",
              "anchor": ""}),
            (("file://file", False, True),
             {"scheme": "file",
              "path": "",
              "file": "file",
              "params": "",
              "query": "",
              "anchor": ""}),
        )
        for test, expected_output in tests:
            result = urlfunctions.url_split(*test)
            for key in expected_output.keys():
                self.assertEqual(getattr(result, key), expected_output[key])

    def test_url_splice(self):
        """Test url_splice."""
        tests = (
            (("file://C:/test/file",
              "file://C:/test/file/some/other/dir",
              "file://C:/test/"),
             "file://C:/test/some/other/dir",
             ),
            (("file://C:/test/file",
              "file://C:/test/file/some/other/dir",
              "ftp://C:/test/"),
             "ftp://C:/test/some/other/dir",
             ),
            (("file://C:/test/file",
              "file://C:/test/file/some/other/dir",
              "file://C:/test/"),
             "file://C:/test/some/other/dir",
             ),
            (("file://C:/test/file/",
              "file://C:/test/file/some/other/dir/",
              "file://C:/test/"),
             "file://C:/test/some/other/dir/",
             ),
            (("file://C:/test/file/",
              "file://C:/test/file/some/other/dir",
              "file://C:/test"),
             "file://C:/test/some/other/dir",
             ),
            (("ftp://C:/test/file",
              "ftp://C:/test/file/some/other/dir",
              "file://C:/test/"),
             "file://C:/test/some/other/dir",
             ),
            (("ftp://C:/test/file",
              "ftp://C:/test/file/some/other/dir",
              "file://C:/test"),
             "file://C:/test/some/other/dir",
             ),
            (("ftp://myhost:21/test/",
              "ftp://myhost:21/test/file",
              "file://otherhost:21/test;someparams"),
             "file://otherhost:21/test/file;someparams",
             ),
            (("ftp://user:pass@myhost:21/test/",
              "ftp://user:pass@myhost:21/test/file",
              "file://otherhost:21/test;someparams"),
             "file://otherhost:21/test/file;someparams",
             ),
        )
        for test, expected_output in tests:
            self.assertEqual(urlfunctions.url_splice(*test), expected_output)

    def test_urls(self):
        """Test URL normalisation."""
        urls = (
            ("C:\\test\\file", "file://C:/test/file"),
            ("C:\\test\\directory\\", "file://C:/test/directory/"),
            ("file", "file://file"),
            ("/root/file", "file:///root/file"),
            ("/root/dir/", "file:///root/dir/"),
        )
        for test, expected_output in urls:
            self.assertEqual(urlfunctions.normalise_url(test), expected_output)

if __name__ == '__main__':
    unittest.main()
