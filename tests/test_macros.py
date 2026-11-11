"""Sanity render of _share.html macros — verify HTML shape."""

from __future__ import annotations

import json
import re

import pytest
from jinja2 import ChoiceLoader, Environment, FileSystemLoader

from krizky_share.plugin import _PLUGIN_TEMPLATES, _share_links


@pytest.fixture
def env():
    e = Environment(
        loader=ChoiceLoader([FileSystemLoader(str(_PLUGIN_TEMPLATES))]),
        autoescape=True,
    )
    e.globals["share_links"] = _share_links({})
    return e


# ---------------------------------------------------------------------------
# share_meta
# ---------------------------------------------------------------------------


def test_share_meta_default_type(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_meta %}'
        '{{ share_meta("https://x.cz/a", "Title", description="Desc", image="https://x.cz/i.jpg") }}'
    )
    out = tmpl.render()
    assert '<meta property="og:type" content="website">' in out
    assert '<meta property="og:url" content="https://x.cz/a">' in out
    assert '<meta property="og:title" content="Title">' in out
    assert '<meta property="og:description" content="Desc">' in out
    assert '<meta property="og:image" content="https://x.cz/i.jpg">' in out
    assert '<meta name="twitter:title" content="Title">' in out
    assert '<link rel="canonical" href="https://x.cz/a">' in out


def test_share_meta_article_type(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_meta %}'
        '{{ share_meta("https://x.cz/a", "T", type="article") }}'
    )
    assert '<meta property="og:type" content="article">' in tmpl.render()


def test_share_meta_omits_optional_fields(env):
    tmpl = env.from_string('{% from "_share.html" import share_meta %}{{ share_meta("u", "t") }}')
    out = tmpl.render()
    assert "og:description" not in out
    assert "og:image" not in out


# ---------------------------------------------------------------------------
# share_schema_place
# ---------------------------------------------------------------------------


def _extract_jsonld(html: str) -> dict:
    m = re.search(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL)
    assert m, f"no JSON-LD in output: {html!r}"
    return json.loads(m.group(1))


def test_schema_place_basic(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_schema_place %}'
        '{{ share_schema_place("Place", "Kříž u Muzika") }}'
    )
    data = _extract_jsonld(tmpl.render())
    assert data["@context"] == "https://schema.org"
    assert data["@type"] == "Place"
    assert data["name"] == "Kříž u Muzika"


def test_schema_place_with_geo(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_schema_place %}'
        '{{ share_schema_place("LandmarksOrHistoricalBuilding", "K", latitude=49.5, longitude=17.9) }}'
    )
    data = _extract_jsonld(tmpl.render())
    assert data["geo"] == {"@type": "GeoCoordinates", "latitude": 49.5, "longitude": 17.9}


def test_schema_place_with_image(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_schema_place %}'
        '{{ share_schema_place("Place", "K", image="https://cdn.x.cz/007.jpg") }}'
    )
    data = _extract_jsonld(tmpl.render())
    assert data["image"] == ["https://cdn.x.cz/007.jpg"]


def test_schema_place_omits_geo_when_partial(env):
    """Chybí longitude → geo se nevygeneruje (validní JSON-LD)."""
    tmpl = env.from_string(
        '{% from "_share.html" import share_schema_place %}'
        '{{ share_schema_place("Place", "K", latitude=49.5) }}'
    )
    data = _extract_jsonld(tmpl.render())
    assert "geo" not in data


# ---------------------------------------------------------------------------
# share_buttons
# ---------------------------------------------------------------------------


def test_share_buttons_renders_desktop_and_mobile_variants(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_buttons %}'
        '{{ share_buttons("https://x.cz/a", "T", image="https://x.cz/i.jpg") }}'
    )
    out = tmpl.render()
    assert 'class="share-desktop"' in out
    assert 'class="share-mobile"' in out
    # 4 desktop icons + 4 mobile menu items + 1 copy button.
    assert out.count('class="share-icon"') == 4
    assert out.count('class="share-menu-item"') == 5  # 4 networks + copy


def test_share_buttons_without_image_hides_pinterest(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_buttons %}{{ share_buttons("https://x.cz/a", "T") }}'
    )
    out = tmpl.render()
    assert "i-share-pinterest" not in out
    assert out.count('class="share-icon"') == 3  # facebook, whatsapp, twitter


def test_share_buttons_data_attributes(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_buttons %}'
        '{{ share_buttons("https://x.cz/a", "Titulek") }}'
    )
    out = tmpl.render()
    assert 'data-share-url="https://x.cz/a"' in out
    assert 'data-share-title="Titulek"' in out


def test_share_buttons_custom_label(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_buttons %}'
        '{{ share_buttons("u", "t", label="Poslat dál") }}'
    )
    out = tmpl.render()
    assert "Poslat dál" in out


def test_share_buttons_label_none_hides_desktop_label_only(env):
    """label=none = jen ikony na desktopu; mobil má stále "Sdílet"."""
    tmpl = env.from_string(
        '{% from "_share.html" import share_buttons %}{{ share_buttons("u", "t", label=none) }}'
    )
    out = tmpl.render()
    # Desktop label element chybí.
    assert 'class="share-label' not in out
    # Mobilní "Sdílet" text a aria-label zůstávají.
    assert "<span>Sdílet</span>" in out
    assert 'aria-label="Sdílet"' in out


def test_share_buttons_copy_button_has_data_attr(env):
    tmpl = env.from_string(
        '{% from "_share.html" import share_buttons %}{{ share_buttons("u", "t") }}'
    )
    assert "data-share-copy" in tmpl.render()
