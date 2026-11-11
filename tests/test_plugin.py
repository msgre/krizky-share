"""Tests for krizky_share.plugin — hookimpl wiring."""

from __future__ import annotations

from krizky_share.plugin import SharePlugin, _share_links

# ---------------------------------------------------------------------------
# _share_links global
# ---------------------------------------------------------------------------


def test_share_links_returns_all_networks_when_image_present():
    fn = _share_links({})
    links = fn("https://x.cz/a", "Titulek", image="https://x.cz/i.jpg")
    keys = [l["network"] for l in links]
    assert keys == ["facebook", "whatsapp", "pinterest", "twitter"]


def test_share_links_skips_pinterest_without_image():
    fn = _share_links({})
    links = fn("https://x.cz/a", "Titulek")
    keys = [l["network"] for l in links]
    assert "pinterest" not in keys
    assert set(keys) == {"facebook", "whatsapp", "twitter"}


def test_share_links_dict_shape():
    fn = _share_links({})
    link = fn("https://x.cz/a", "T")[0]
    assert set(link.keys()) == {"network", "label", "icon", "url"}
    assert link["icon"].startswith("i-share-")


def test_share_links_respects_configured_networks():
    fn = _share_links({"site": {"share": {"networks": ["twitter"]}}})
    links = fn("https://x.cz/a", "T")
    assert [l["network"] for l in links] == ["twitter"]


# ---------------------------------------------------------------------------
# inject_head
# ---------------------------------------------------------------------------


def test_inject_head_emits_site_defaults():
    plugin = SharePlugin()
    html = plugin.inject_head(
        page_cfg={},
        config={"site": {"title": "Valašské nebe", "language": "cs"}},
    )
    assert '<meta property="og:site_name" content="Valašské nebe">' in html
    assert '<meta property="og:locale" content="cs">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html
    assert '<link rel="stylesheet" href="/krizky-share/share.css">' in html


def test_inject_head_converts_bcp47_to_og_locale():
    """site.language 'cs-CZ' (BCP 47) → og:locale 'cs_CZ' (Facebook convention)."""
    plugin = SharePlugin()
    html = plugin.inject_head(
        page_cfg={},
        config={"site": {"title": "T", "language": "cs-CZ"}},
    )
    assert '<meta property="og:locale" content="cs_CZ">' in html


def test_inject_head_twitter_site_when_configured():
    plugin = SharePlugin()
    html = plugin.inject_head(
        page_cfg={},
        config={"site": {"title": "T", "share": {"twitter_site": "@valasskenebe"}}},
    )
    assert '<meta name="twitter:site" content="@valasskenebe">' in html


def test_inject_head_default_image_absolutized_when_base_url_present():
    plugin = SharePlugin()
    html = plugin.inject_head(
        page_cfg={},
        config={
            "site": {
                "title": "T",
                "base_url": "https://valasskenebe.cz",
                "share": {"default_image": "/assets/og.jpg"},
            }
        },
    )
    assert '<meta property="og:image" content="https://valasskenebe.cz/assets/og.jpg">' in html


def test_inject_head_default_image_passes_absolute_url_through():
    plugin = SharePlugin()
    html = plugin.inject_head(
        page_cfg={},
        config={
            "site": {
                "title": "T",
                "base_url": "https://valasskenebe.cz",
                "share": {"default_image": "https://cdn.example.com/og.jpg"},
            }
        },
    )
    assert '<meta property="og:image" content="https://cdn.example.com/og.jpg">' in html


def test_inject_head_escapes_html_in_values():
    plugin = SharePlugin()
    html = plugin.inject_head(
        page_cfg={},
        config={"site": {"title": 'A "B" & <C>'}},
    )
    assert 'content="A &quot;B&quot; &amp; &lt;C&gt;"' in html


# ---------------------------------------------------------------------------
# inject_body_end
# ---------------------------------------------------------------------------


def test_inject_body_end_contains_sprite_and_script():
    plugin = SharePlugin()
    html = plugin.inject_body_end(page_cfg={}, config={})
    # Sprite has all 6 symbols with i-share-* IDs.
    for icon in ("toggle", "facebook", "whatsapp", "pinterest", "twitter", "copy"):
        assert f'id="i-share-{icon}"' in html
    assert '<script src="/krizky-share/share.js" defer></script>' in html


# ---------------------------------------------------------------------------
# after_page_written — assets copy
# ---------------------------------------------------------------------------


def test_after_page_written_copies_assets(tmp_path):
    plugin = SharePlugin()
    plugin.after_page_written(
        page_cfg={},
        html_path="/foo.html",
        output_dir=tmp_path,
        records=[],
        config={},
    )
    assert (tmp_path / "krizky-share" / "share.css").exists()
    assert (tmp_path / "krizky-share" / "share.js").exists()


def test_after_page_written_copies_only_once(tmp_path):
    """Second call for the same output_dir doesn't rewrite assets."""
    plugin = SharePlugin()
    plugin.after_page_written(
        page_cfg={}, html_path="/a.html", output_dir=tmp_path, records=[], config={}
    )
    mtime_before = (tmp_path / "krizky-share" / "share.css").stat().st_mtime_ns
    plugin.after_page_written(
        page_cfg={}, html_path="/b.html", output_dir=tmp_path, records=[], config={}
    )
    mtime_after = (tmp_path / "krizky-share" / "share.css").stat().st_mtime_ns
    assert mtime_before == mtime_after
