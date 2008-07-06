"""omnisync unit tests."""

import unittest
import omnisync

class Tests(unittest.TestCase):
    """Various omnisync unit tests."""

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
