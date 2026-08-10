"""
Fresh-information research for ALF.

Provides a small boundary between ALF and external information sources.
"""

from html.parser import HTMLParser
from urllib.request import Request, urlopen

from .identity import get_identity


class TextExtractor(HTMLParser):
    """
    Extract readable text from HTML content.
    """

    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignored_elements = set()

    def handle_starttag(self, tag, attrs):
        if tag in {"style", "script"}:
            self.ignored_elements.add(tag)

    def handle_endtag(self, tag):
        self.ignored_elements.discard(tag)

    def handle_data(self, data):
        if not self.ignored_elements:
            self.parts.append(data)

    def get_text(self):
        return " ".join(" ".join(self.parts).split())


def fetch(url):
    """
    Fetch text content from an external URL.
    """

    identity = get_identity()

    request = Request(
        url,
        headers={"User-Agent": f"{identity['name']}/{identity['version']}"},
    )

    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


def extract_text(html):
    """
    Extract readable text from HTML content.
    """

    parser = TextExtractor()
    parser.feed(html)

    return parser.get_text()
