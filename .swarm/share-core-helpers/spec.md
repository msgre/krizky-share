# Specifikace: share-core-helpers

- **Repo:** `krizky-share`
- **Zdroj:** konsolidace do core, rozhodnuto 2026-11-13. Core v běhu `plugin-helpers` (`/Users/msgre/projects/muzeum/krizky/.swarm/plugin-helpers/spec.md`) přidal hook `copy_plugin_assets` a modul `krizky.plugin_helpers` s funkcemi `register_plugin_templates` a `replace_tree`. Core má verzi 0.2.0.
- **Předpoklad:** běh `plugin-helpers` je sloučený v `main` repa `msgre/krizky`.

## Cíl

Plugin přestane opakovat kód, který převzal core: registraci šablon a kopírování assetů s vlastním hlídáním opakování. Chování pro uživatele zůstane stejné, až na změnu v části 3.

## 1. Závislost na core 0.2

- `pyproject.toml`: `krizky>=0.2`.
- `uv lock --upgrade-package krizky`, aby `uv.lock` obsahoval core s `plugin_helpers`.

**Akceptace:** `uv.lock` obsahuje `krizky` ve verzi 0.2.0 nebo vyšší.

## 2. Registrace šablon

- `prepare_jinja2_environment` volá `register_plugin_templates(env, _PLUGIN_TEMPLATES)` místo vlastní manipulace s `ChoiceLoader`. Registrace globálu `share_links` zůstává.
- Import `ChoiceLoader` a `FileSystemLoader` zmizí.

**Akceptace:** stávající testy registrace šablon a `share_links` projdou, v `plugin.py` není `ChoiceLoader`.

## 3. Kopírování assetů přes hook `copy_plugin_assets`

- Nový `@hookimpl copy_plugin_assets(self, output_dir, config, config_dir)`: `replace_tree(_PLUGIN_ASSETS / "krizky-share", output_dir / "krizky-share")`.
- Odstranit `after_page_written` (už nic nedělá), `_copy_assets` a `_assets_copied`.

**Změny chování (záměrné):**
- `output/krizky-share/` se při každém buildu vytvoří znovu, takže v něm nezůstanou staré soubory.
- Do výstupu se zkopíruje i `icons.svg` (dnes se kopírují jen `share.css` a `share.js`). Nevadí to, soubor je malý.

**Akceptace (testy):**
- `copy_plugin_assets` zkopíruje `share.css` a `share.js` do `output_dir/krizky-share/`.
- Soubor, který v `output_dir/krizky-share/` zůstal z dřívějška, po volání zmizí.
- Plugin nemá hookimpl `after_page_written`.

## 4. Dokumentace (docs-sync)

- `README.md`: seznam hooků (pokud je) upravit: přibude `copy_plugin_assets`, ubude `after_page_written`.

**Akceptace:** `scripts/verify` projde.

## Mimo rozsah

- CSS tokeny bez prefixu `--krizky-*` (revize, `plugin-krizky-share.md`).
