"""Share network definitions: URL templates, labels, availability rules.

Each network is a small dict; :func:`build_share_link` renders the final URL
with the caller's ``url`` / ``title`` / ``image`` parameters.
"""

from urllib.parse import quote

# Supported networks in stable order. Config `networks:` picks and reorders.
NETWORKS: dict[str, dict] = {
    "facebook": {
        "label": "Facebook",
        "icon": "i-share-facebook",
        "url_template": "https://www.facebook.com/sharer/sharer.php?u={url}",
        "requires_image": False,
    },
    "whatsapp": {
        "label": "WhatsApp",
        "icon": "i-share-whatsapp",
        # WhatsApp needs title and URL in a single text parameter.
        "url_template": "https://wa.me/?text={title}%20{url}",
        "requires_image": False,
    },
    "pinterest": {
        "label": "Pinterest",
        "icon": "i-share-pinterest",
        "url_template": (
            "https://pinterest.com/pin/create/button/?url={url}&media={image}&description={title}"
        ),
        "requires_image": True,
    },
    "twitter": {
        "label": "X (Twitter)",
        "icon": "i-share-twitter",
        "url_template": "https://twitter.com/intent/tweet?url={url}&text={title}",
        "requires_image": False,
    },
}


def build_share_link(
    network: str,
    url: str,
    title: str,
    image: str | None = None,
) -> str | None:
    """Return the share URL for *network* or ``None`` if the network can't be used.

    Returns ``None`` when the network requires an image (Pinterest) and none
    was supplied. This lets the caller silently skip the button.
    """
    cfg = NETWORKS.get(network)
    if cfg is None:
        raise ValueError(f"Unknown share network: {network!r}")
    if cfg["requires_image"] and not image:
        return None
    return cfg["url_template"].format(
        url=quote(url, safe=""),
        title=quote(title, safe=""),
        image=quote(image or "", safe=""),
    )


def resolve_networks(config: dict) -> list[str]:
    """Return the list of network keys to render, in config order.

    Default: all supported networks in :data:`NETWORKS` order.
    """
    share_cfg = config.get("site", {}).get("share", {}) or {}
    configured = share_cfg.get("networks")
    if not configured:
        return list(NETWORKS)
    # Preserve user's order; skip unknown networks silently (log-worthy but not fatal).
    return [n for n in configured if n in NETWORKS]
