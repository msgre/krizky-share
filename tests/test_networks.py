"""Tests for krizky_share.networks — URL builders and network resolution."""

from urllib.parse import parse_qs, urlparse

import pytest

from krizky_share.networks import NETWORKS, build_share_link, resolve_networks

# ---------------------------------------------------------------------------
# build_share_link
# ---------------------------------------------------------------------------


def _q(url: str, param: str) -> str:
    return parse_qs(urlparse(url).query)[param][0]


def test_facebook_url_contains_encoded_page_url():
    url = build_share_link("facebook", "https://valasskenebe.cz/kriz.html", "Kříž")
    assert url.startswith("https://www.facebook.com/sharer/sharer.php?u=")
    assert _q(url, "u") == "https://valasskenebe.cz/kriz.html"


def test_twitter_url_contains_url_and_text():
    url = build_share_link("twitter", "https://x.cz/a", "Titulek")
    assert _q(url, "url") == "https://x.cz/a"
    assert _q(url, "text") == "Titulek"


def test_whatsapp_url_encodes_title_and_url():
    url = build_share_link("whatsapp", "https://x.cz/a", "Kříž & socha")
    text = _q(url, "text")
    # WhatsApp text = "{title} {url}" — both must be URL-encoded.
    assert "https://x.cz/a" in text
    assert "Kříž & socha" in text  # decoded back by parse_qs


def test_pinterest_requires_image_returns_none_without():
    result = build_share_link("pinterest", "https://x.cz/a", "Titulek", image=None)
    assert result is None


def test_pinterest_with_image_builds_url():
    url = build_share_link(
        "pinterest",
        "https://x.cz/a",
        "Titulek",
        image="https://cdn.example.com/007.jpg",
    )
    assert url is not None
    assert _q(url, "url") == "https://x.cz/a"
    assert _q(url, "media") == "https://cdn.example.com/007.jpg"
    assert _q(url, "description") == "Titulek"


def test_unknown_network_raises():
    with pytest.raises(ValueError, match="Unknown share network"):
        build_share_link("mastodon", "https://x.cz", "T")


def test_special_chars_are_url_encoded():
    """Query strings / hashes / spaces must be percent-encoded."""
    url = build_share_link("facebook", "https://x.cz/a?b=1&c=d#e", "T&U")
    assert _q(url, "u") == "https://x.cz/a?b=1&c=d#e"
    # Raw ampersands from title must not appear unencoded before the next param.
    assert "?u=https%3A%2F%2F" in url


# ---------------------------------------------------------------------------
# resolve_networks
# ---------------------------------------------------------------------------


def test_resolve_networks_default_returns_all():
    assert resolve_networks({}) == list(NETWORKS)


def test_resolve_networks_respects_config_order():
    config = {"site": {"share": {"networks": ["twitter", "facebook"]}}}
    assert resolve_networks(config) == ["twitter", "facebook"]


def test_resolve_networks_skips_unknown():
    config = {"site": {"share": {"networks": ["facebook", "mastodon", "whatsapp"]}}}
    assert resolve_networks(config) == ["facebook", "whatsapp"]


def test_resolve_networks_empty_list_falls_back_to_all():
    """Empty networks list is treated as unset (default all)."""
    config = {"site": {"share": {"networks": []}}}
    assert resolve_networks(config) == list(NETWORKS)
