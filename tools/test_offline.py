import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from check_feeds import parse_date, parse_feed  # noqa: E402
from discover_feeds import find_alternates  # noqa: E402

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Test</title>
<item><title>A</title><pubDate>Thu, 29 Oct 2026 08:00:00 +0100</pubDate></item>
<item><title>B</title><pubDate>Wed, 28 Oct 2026 08:00:00 GMT</pubDate></item></channel></rss>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>At</title>
<entry><title>X</title><updated>2026-10-29T06:00:00Z</updated></entry></feed>"""


class Tests(unittest.TestCase):
    def test_rss(self):
        title, n, newest = parse_feed(RSS)
        self.assertEqual((title, n), ("Test", 2))
        self.assertEqual(newest.day, 29)

    def test_atom(self):
        title, n, newest = parse_feed(ATOM)
        self.assertEqual((title, n, newest.hour), ("At", 1, 6))

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_feed(b"<html><body>pas un flux</body></html>")
        with self.assertRaises(ValueError):
            parse_feed(b"pas du xml")

    def test_dates(self):
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date("hier"))

    def test_alternates(self):
        html = ('<link rel="alternate" type="application/rss+xml" href="/rss/une.xml">'
                '<link rel="alternate" type="application/atom+xml" href="https://x.fr/a?b=1&amp;c=2">'
                '<link rel="alternate" type="application/rss+xml" href="/comments/feed">'
                '<link rel="stylesheet" href="/s.css">')
        got = find_alternates(html, "https://www.exemple.fr/politique/")
        self.assertEqual(got, ["https://www.exemple.fr/rss/une.xml", "https://x.fr/a?b=1&c=2"])


if __name__ == "__main__":
    unittest.main()
