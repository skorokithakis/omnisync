"""omnisync unit tests."""

import unittest
import omnisync
import urlfunctions

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

    def test_url_split(self):
        """Test url_split."""
        tests = (
            ("file://some/file", ("file://some/", "file")),
            ("file://some/dir/", ("file://some/dir/", "")),
            ("file://dir", ("file://dir/", "")),
            ("file://dir/", ("file://dir/", "")),
        )
        for test, expected_output in tests:
            self.assertEqual(urlfunctions.url_split(test), expected_output)

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
            (("ftp://C:/test/",
              "ftp://C:/test/file",
              "file://C:/test"),
             "file://C:/test/file",
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
            self.assertEqual(omnisync.normalise_url(test), expected_output)

if __name__ == '__main__':
    unittest.main()
