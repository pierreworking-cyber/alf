"""
Fresh-information research for ALF.

Provides a small boundary between ALF and external information sources.
"""

from urllib.request import Request, urlopen

from .identity import get_identity


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
