# krizky-share

Plugin pro [krizky](https://github.com/msgre/krizky) přidávající meta tagy pro sociální sítě (Open Graph, Twitter Cards), Schema.org strukturovaná data (Place, LandmarksOrHistoricalBuilding, …) a Jinja2 makro pro sdílecí widget (Facebook, WhatsApp, Pinterest, X/Twitter + Kopírovat odkaz).

## Instalace

```bash
pip install krizky-share
```

Aktivuje se automaticky přes entry point.

## Konfigurace

Do `config.yaml`:

```yaml
site:
  base_url: https://valasskenebe.cz    # povinné pro absolutní URL
  share:
    twitter_site: '@valasskenebe'      # optional — twitter:site meta
    default_image: /assets/og.jpg      # optional — fallback og:image (relativní k base_url)
    networks:                          # optional — pořadí a filtr sítí; default = vše
      - facebook
      - whatsapp
      - pinterest
      - twitter
```

Bez sekce `share:` plugin běží s defaulty (všechny sítě, žádné vlastní twitter_site / default_image).

`og:locale` se odvozuje z `site.language` (BCP 47 pomlčka → OG podtržítko, např. `cs-CZ` → `cs_CZ`).

## Nutné úpravy šablon

Aby se meta tagy a assety zobrazily, `base.html` potřebuje standardní krizky injekce a jeden extra block:

```html
<head>
  ...
  {{ head_injections | safe }}
  {% block extra_meta %}{% endblock %}
</head>
<body>
  ...
  {{ body_end_injections | safe }}
</body>
```

## Použití v šablonách

### Meta tagy (per stránka)

```jinja2
{% from "_share.html" import share_meta %}
{% set page_url = absolute_url('/' ~ record.slug ~ '.html') %}

{% block extra_meta %}
  {{ share_meta(page_url, record.nazev,
       description=record.pribeh|truncate(160),
       image=absolute_url(photos(record.id_radku).primary.variants.big.url) if photos(record.id_radku).has_photos else none,
       type="article") }}
{% endblock %}
```

`share_meta()` parametry:

| Parametr | Popis |
|---|---|
| `url` | absolutní URL stránky (`absolute_url(...)`) |
| `title` | titulek — record.nazev / site.title |
| `description` | popis (optional) |
| `image` | absolutní URL obrázku (optional) |
| `type` | og:type — default `"website"`, pro detaily použij `"article"` |

Site-wide fallbacky (og:site_name, og:locale, twitter:card, twitter:site, default og:image) plugin automaticky vloží přes `head_injections`.

### Schema.org JSON-LD (typicky pro detail)

```jinja2
{% from "_share.html" import share_schema_place %}

{{ share_schema_place("LandmarksOrHistoricalBuilding",
    name=record.nazev,
    description=record.pribeh,
    latitude=record.latitude, longitude=record.longitude,
    image=absolute_url(photos(record.id_radku).primary.variants.big.url) if photos(record.id_radku).has_photos else none,
    url=absolute_url('/' ~ record.slug ~ '.html')
) }}
```

Vyprodukuje `<script type="application/ld+json">…</script>`. Typ vyber podle povahy záznamu:
- `"Place"` — obecné místo
- `"LandmarksOrHistoricalBuilding"` — památník / historická stavba
- `"Sculpture"` — socha
- kompletní seznam: [schema.org/Place](https://schema.org/Place)

### Sdílecí tlačítka

```jinja2
{% from "_share.html" import share_buttons %}
{{ share_buttons(page_url, record.nazev,
     image=absolute_url(photos(record.id_radku).primary.variants.big.url) if photos(record.id_radku).has_photos else none) }}
```

- **Desktop** (≥ 640px): řada 4 kruhových ikon podle konfigurovaných sítí.
- **Mobil** (< 640px): jedno tlačítko „Sdílet". S JS zavolá `navigator.share()` (nativní OS share). Bez JS se otevře fallback dropdown s explicit odkazy + „Kopírovat odkaz".
- **Pinterest** se skryje, pokud `image=none`.

## Assety

Plugin generuje do output:

```
/krizky-share/share.css
/krizky-share/share.js
```

Vkládají se automaticky do `<head>` (CSS) a před `</body>` (JS + inline SVG sprite).

## Design

CSS vychází z tokenů projektu Valašské nebe (`--surface`, `--hairline`, `--muted`, `--ink`, `--radius`, `--mono`). Pokud tvůj projekt tyhle proměnné nemá, komponenty budou vypadat jinak — nastavením barev v `assets/css/style.css` nebo přepsáním tříd (`.share-icon`, `.share-toggle`, `.share-menu`, …) si widget upravíš.

## Licence

MIT
