from app.ingestion.discovery import parse_index_html, robots_allowed


def test_robots_and_index_parser():
    robots = "User-agent: *\nDisallow: /private\nAllow: /overlord/\n"
    assert robots_allowed(robots, "https://example.com/overlord/", "OverlordNovelEngine/0.1")
    assert not robots_allowed(robots, "https://example.com/private/chapter", "OverlordNovelEngine/0.1")
    links = parse_index_html(
        "<html><h1>Overlord</h1><a href='/overlord/vol-16'>Tập 16</a><p>This long body must not be stored as a chapter.</p></html>",
        "https://example.com/overlord/",
    )
    assert links[0].title == "Tập 16"
    assert links[0].url == "https://example.com/overlord/vol-16"
    assert all("long body" not in link.title for link in links)
