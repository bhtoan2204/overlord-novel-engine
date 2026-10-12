"""Metadata discovery. Stores titles and links only, and honors robots.txt."""

import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.core.errors import EngineError


@dataclass
class DiscoveredLink:
    title: str
    url: str
    heading: str


def robots_allowed(robots_txt: str, url: str, user_agent: str) -> bool:
    parser = RobotFileParser()
    parser.parse(robots_txt.splitlines())
    return parser.can_fetch(user_agent, url)


def parse_index_html(html: str, base_url: str) -> list[DiscoveredLink]:
    soup = BeautifulSoup(html, "lxml")
    heading = ""
    h1 = soup.find("h1")
    if h1:
        heading = " ".join(h1.get_text(" ", strip=True).split())[:200]
    found: list[DiscoveredLink] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        title = " ".join(anchor.get_text(" ", strip=True).split())
        if not title or len(title) > 200:
            continue
        absolute = urljoin(base_url, anchor["href"])
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        found.append(DiscoveredLink(title=title, url=absolute, heading=heading))
    return found


def discover_index(
    url: str,
    user_agent: str,
    rate_limit_seconds: float = 2.0,
    client: httpx.Client | None = None,
) -> tuple[str, list[DiscoveredLink]]:
    """Fetch robots.txt and, only if allowed, the index page's titles and links.

    Chapter bodies are not stored. Callers persist DiscoveredLink records only.
    """
    owns_client = client is None
    client = client or httpx.Client(timeout=20.0, headers={"User-Agent": user_agent}, follow_redirects=True)
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise EngineError("Discovery only accepts http and https URLs.")
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        robots_response = client.get(robots_url)
        robots_text = robots_response.text if robots_response.status_code == 200 else "User-agent: *\nAllow: /"
        if not robots_allowed(robots_text, url, user_agent):
            return "disallowed", []
        time.sleep(max(0.0, rate_limit_seconds))
        page = client.get(url)
        page.raise_for_status()
        return "allowed", parse_index_html(page.text, url)
    finally:
        if owns_client:
            client.close()
