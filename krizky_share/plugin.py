"""krizky-share plugin — hook implementations."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from jinja2 import ChoiceLoader, FileSystemLoader

from krizky.hooks import hookimpl
from krizky_share.networks import NETWORKS, build_share_link, resolve_networks

_log = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).parent
_PLUGIN_TEMPLATES = _PLUGIN_DIR / "templates"
_PLUGIN_ASSETS = _PLUGIN_DIR / "assets"
_ICONS_SVG = _PLUGIN_ASSETS / "krizky-share" / "icons.svg"


def _share_links(config: dict):
    """Return a Jinja2 global that builds share link dicts for a given URL/title/image.

    Each dict: ``{"network": str, "label": str, "icon": str, "url": str}``.
    Networks that can't be built (e.g. Pinterest without image) are silently skipped.
    """
    network_keys = resolve_networks(config)

    def _links(url: str, title: str, image: str | None = None) -> list[dict]:
        out: list[dict] = []
        for key in network_keys:
            share_url = build_share_link(key, url, title, image)
            if share_url is None:
                continue
            cfg = NETWORKS[key]
            out.append({
                "network": key,
                "label": cfg["label"],
                "icon": cfg["icon"],
                "url": share_url,
            })
        return out

    return _links


class SharePlugin:
    """Social sharing plugin for krizky.

    Hooks:
    - prepare_jinja2_environment: registers plugin templates and share_links() global
    - inject_head: emits site-wide OG defaults (og:site_name, og:locale, twitter:site, default image)
    - inject_body_end: injects the SVG icon sprite
    - after_page_written: copies CSS/JS assets into the output directory
    """

    def __init__(self) -> None:
        self._assets_copied: set[str] = set()

    # ------------------------------------------------------------------
    # prepare_jinja2_environment
    # ------------------------------------------------------------------

    @hookimpl
    def prepare_jinja2_environment(self, env, config, config_dir):
        """Insert plugin templates into the loader chain and register share_links global."""
        if isinstance(env.loader, ChoiceLoader):
            loaders = env.loader.loaders
            already = any(
                isinstance(ldr, FileSystemLoader) and str(_PLUGIN_TEMPLATES) in ldr.searchpath
                for ldr in loaders
            )
            if not already:
                # After project templates, before built-in krizky templates.
                env.loader.loaders = (
                    [loaders[0], FileSystemLoader(str(_PLUGIN_TEMPLATES))] + loaders[1:]
                )
        env.globals["share_links"] = _share_links(config)

    # ------------------------------------------------------------------
    # inject_head — site-wide OG/Twitter defaults
    # ------------------------------------------------------------------

    @hookimpl
    def inject_head(self, page_cfg, config):
        """Emit invariant site-wide OG/Twitter meta tags.

        Per-page tags (og:type, og:url, og:title, og:description, og:image) are
        left to the template via the ``share_meta()`` macro so it can use record
        data. This hook only fills in globals that apply to every page:
        og:site_name, og:locale, twitter:site, twitter:card, default og:image.
        """
        site = config.get("site", {})
        share_cfg = site.get("share", {}) or {}

        parts: list[str] = []

        site_title = site.get("title", "").strip()
        if site_title:
            parts.append(f'<meta property="og:site_name" content="{_esc(site_title)}">')

        # og:locale expects "language_TERRITORY" (underscore). site.language is BCP 47
        # (hyphen, e.g. "cs-CZ"). Derive og:locale automatically — no separate config.
        locale = site.get("language", "").strip().replace("-", "_")
        if locale:
            parts.append(f'<meta property="og:locale" content="{_esc(locale)}">')

        parts.append('<meta name="twitter:card" content="summary_large_image">')

        twitter_site = share_cfg.get("twitter_site")
        if twitter_site:
            parts.append(f'<meta name="twitter:site" content="{_esc(twitter_site)}">')

        default_image = share_cfg.get("default_image")
        if default_image:
            # Resolve to absolute URL when base_url is configured; otherwise pass through.
            base_url = site.get("base_url", "").rstrip("/")
            if base_url and default_image.startswith("/"):
                default_image = f"{base_url}{default_image}"
            parts.append(f'<meta property="og:image" content="{_esc(default_image)}">')

        parts.append('<link rel="stylesheet" href="/krizky-share/share.css">')

        return "\n".join(parts) + "\n" if parts else None

    # ------------------------------------------------------------------
    # inject_body_end — SVG sprite + JS
    # ------------------------------------------------------------------

    @hookimpl
    def inject_body_end(self, page_cfg, config):
        """Inline the SVG icon sprite and the share.js script tag."""
        pieces: list[str] = []
        try:
            pieces.append(_ICONS_SVG.read_text(encoding="utf-8").rstrip())
        except OSError:
            _log.warning("krizky-share sprite not found: %s", _ICONS_SVG)
        pieces.append('<script src="/krizky-share/share.js" defer></script>')
        return "\n".join(pieces) + "\n"

    # ------------------------------------------------------------------
    # after_page_written — copy CSS/JS assets
    # ------------------------------------------------------------------

    @hookimpl
    def after_page_written(self, page_cfg, html_path, output_dir, records, config):
        """Copy share.css + share.js into output/krizky-share/ (once per build)."""
        self._copy_assets(output_dir)

    def _copy_assets(self, output_dir: Path) -> None:
        key = str(output_dir)
        if key in self._assets_copied:
            return
        dst = output_dir / "krizky-share"
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("share.css", "share.js"):
            src = _PLUGIN_ASSETS / "krizky-share" / name
            if src.exists():
                shutil.copy2(src, dst / name)
        self._assets_copied.add(key)


def _esc(value: str) -> str:
    """Minimal HTML attribute escaping for values injected into <meta>."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


plugin = SharePlugin()
