# krizky-share — implementační plán

## Co je cílem

Plugin do krizky, který doplňuje na každou generovanou stránku Open Graph a Twitter Card meta tagy pro sociální sítě, umožňuje šablonám vypsat Schema.org strukturovaná data (Place, LandmarksOrHistoricalBuilding, …) a poskytuje makro pro vykreslení sdílecího widgetu (Facebook, WhatsApp, Pinterest, X/Twitter + Kopírovat odkaz).

## Design principy

- **Explicit ze šablony pro per-record věci.** Hook `inject_head` vypíše jen invariantní site-wide fallbacky (og:site_name, locale, twitter:card/site, default og:image). Per-page a per-record tagy (og:type, og:url, og:title, og:description, og:image, JSON-LD) vypíše šablona voláním maker.
- **Self-contained assety.** Plugin dodává SVG sprite ikon (vytažené z projektového design manuálu), CSS a JS — projekt nic vlastního přidávat nemusí. Prefix `i-share-*` aby ID nekolidovala s uživatelovým sprite.
- **Progressive enhancement.** Bez JavaScriptu jsou tlačítka funkční linky. Mobilní widget je `<details>` + `<summary>` — dropdown funguje bez JS. S JS mobil používá Web Share API a nabízí "Kopírovat odkaz".
- **Pinterest bez fotky se schová.** V helper listu `share_links()` se Pinterest vypíše jen když je předán `image`.

## Struktura

```
krizky-share/
├── PLAN.md
├── README.md
├── pyproject.toml
├── krizky_share/
│   ├── __init__.py
│   ├── plugin.py                       — hookimpl
│   ├── networks.py                     — URL builders + resolve_networks
│   ├── templates/
│   │   └── _share.html                 — share_meta, share_schema_place, share_buttons
│   └── assets/
│       └── krizky-share/
│           ├── icons.svg               — sprite se 6 symboly (i-share-toggle, -facebook,
│           │                             -whatsapp, -pinterest, -twitter, -copy)
│           ├── share.css               — desktop řada + mobil dropdown, breakpoint 640px
│           └── share.js                — Web Share API, copy to clipboard, dropdown toggle
└── tests/
    ├── test_networks.py                — URL buildery, resolve_networks
    ├── test_plugin.py                  — hookimpl (inject_head, inject_body_end, assets copy)
    └── test_macros.py                  — sanity render maker
```

## Hooky

| Hook | Co dělá |
|---|---|
| `prepare_jinja2_environment` | Přidá plugin templates do loaderu; registruje Jinja2 global `share_links(url, title, image)` |
| `inject_head` | Site-wide OG/Twitter defaults + `<link>` na share.css |
| `inject_body_end` | Inline SVG sprite + `<script>` na share.js |
| `after_page_written` | Zkopíruje share.css a share.js do `output/krizky-share/` (jednou per build) |

## Konfigurace (opt-in)

```yaml
site:
  base_url: https://valasskenebe.cz    # nezbytné pro absolutní URL (přidáno do core)
  share:
    twitter_site: '@valasskenebe'      # optional — twitter:site meta
    default_image: /assets/og.jpg      # optional — fallback og:image (relativní k base_url)
    networks:                          # optional — pořadí a filtr; default = [facebook, whatsapp, pinterest, twitter]
      - twitter
      - facebook
```

## Použití v šablonách

**Base layout (`base.html`)** — přidat block do `<head>`:
```jinja2
<head>
  ...
  {{ head_injections | safe }}   {# ← už existuje pro filters plugin, share přispěje taky #}
  {% block extra_meta %}{% endblock %}
</head>
<body>
  ...
  {{ body_end_injections | safe }}
</body>
```

**Detail stránka (`detail.html`)** — vyplní per-record tagy:
```jinja2
{% from "_share.html" import share_meta, share_schema_place, share_buttons %}
{% set page_url = absolute_url('/' ~ record.slug ~ '.html') %}
{% set imgs = photos(record.id_radku) %}
{% set og_image = absolute_url(imgs.primary.variants.big.url) if imgs.has_photos else none %}

{% block extra_meta %}
  {{ share_meta(page_url, record.nazev, description=record.pribeh|truncate(160), image=og_image, type="article") }}
  {{ share_schema_place("LandmarksOrHistoricalBuilding",
       name=record.nazev,
       description=record.pribeh,
       latitude=record.latitude, longitude=record.longitude,
       image=og_image, url=page_url) }}
{% endblock %}

{% block content %}
  ...
  {{ share_buttons(page_url, record.nazev, image=og_image) }}
{% endblock %}
```

**Kategorie / výpis (`kategorie.html`)** — bez schema, jen meta + tlačítka:
```jinja2
{% from "_share.html" import share_meta, share_buttons %}
{% set page_url = absolute_url(page_urls.kategorie) %}   {# nebo rendered path #}
{% block extra_meta %}
  {{ share_meta(page_url, site.page_title, description=site.page_description) }}
{% endblock %}
{% block content %}
  ...
  {{ share_buttons(page_url, site.page_title) }}
{% endblock %}
```

## Závislosti

- `krizky>=0.1` (potřebuje nový `absolute_url()` helper a `site.base_url` — přidáno v prep commitu).
- Bez runtime závislostí (žádné Pillow, boto3, …).

## Testování

- Testy nespoléhají na filesystem projektu — jsou izolované.
- `test_networks.py`: URL kódování, Pinterest bez fotky, `resolve_networks`.
- `test_plugin.py`: `_share_links` global, `inject_head`, `inject_body_end`, kopírování assetů.
- `test_macros.py`: sanity render všech tří maker (meta, schema, buttons).
