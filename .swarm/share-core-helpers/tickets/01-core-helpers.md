---
id: "01"
slug: core-helpers
title: Plugin používá helpery a hook copy_plugin_assets z core 0.2
status: done
depends_on: []
files:
  - pyproject.toml
  - uv.lock
  - krizky_share/plugin.py
  - tests/test_plugin.py
  - README.md
attempts: 1
pr: "2"
---

## Cíl
Plugin přestane opakovat kód, který převzal core 0.2: registraci šablon (`register_plugin_templates`) a kopírování assetů (`replace_tree` v novém hooku `copy_plugin_assets`). Pokrývá celou specifikaci `.swarm/share-core-helpers/spec.md` (části 1–4). Části spolu souvisí, protože obě změny v `plugin.py` potřebují core 0.2 a sdílí stejné soubory, proto jsou v jednom tiketu.

## Akceptační kritéria
- `pyproject.toml` má závislost `krizky>=0.2`.
- `uv.lock` obsahuje `krizky` ve verzi 0.2.0 nebo vyšší (aktualizace přes `uv lock --upgrade-package krizky`). Zamčený commit core obsahuje `krizky/plugin_helpers.py` a hook `copy_plugin_assets` (je v `origin/main` repa `msgre/krizky`, PR #8).
- `prepare_jinja2_environment` volá `register_plugin_templates(env, _PLUGIN_TEMPLATES)` z `krizky.plugin_helpers` a dál registruje globál `share_links`.
- V `krizky_share/plugin.py` není `ChoiceLoader`, `FileSystemLoader` ani `import shutil` (`git grep -n ChoiceLoader -- krizky_share/plugin.py` nic nenajde).
- Nový `@hookimpl copy_plugin_assets(self, output_dir, config, config_dir)` volá `replace_tree(_PLUGIN_ASSETS / "krizky-share", output_dir / "krizky-share")`. `output_dir` může přijít jako `str` i `Path`, obal ho do `Path(...)`.
- Z `SharePlugin` zmizí `after_page_written`, `_copy_assets`, `_assets_copied` i `__init__`, který jen inicializoval `_assets_copied`.
- Docstring třídy `SharePlugin` (seznam hooků) uvádí `copy_plugin_assets` místo `after_page_written`.
- `README.md`, sekce „Assety“: výpis výstupu obsahuje i `/krizky-share/icons.svg` a je tam poznámka, že se adresář `output/krizky-share/` při každém buildu vytvoří znovu.
- `scripts/verify` skončí s exit 0.

## Testy
TDD, nejdřív v `tests/test_plugin.py`:
1. `test_copy_plugin_assets_copies_assets(tmp_path)`: po `SharePlugin().copy_plugin_assets(output_dir=tmp_path, config={}, config_dir=tmp_path)` existují `tmp_path/"krizky-share"/"share.css"` a `"share.js"`.
2. `test_copy_plugin_assets_removes_stale_files(tmp_path)`: předem vytvoř `tmp_path/"krizky-share"/"stale.txt"`, po volání hooku soubor neexistuje.
3. `test_plugin_has_no_after_page_written`: `not hasattr(SharePlugin, "after_page_written")`.
4. `test_prepare_jinja2_environment_registers_templates_and_global`: `Environment(loader=ChoiceLoader([FileSystemLoader(proj), FileSystemLoader(builtin)]))` (adresáře z `tmp_path`). Po volání hooku je na indexu 1 loader se `searchpath` obsahujícím `str(_PLUGIN_TEMPLATES)`, `"share_links" in env.globals`, a druhé volání nepřidá loader znovu (délka seznamu loaderů zůstane 3).

Smaž `test_after_page_written_copies_assets` a `test_after_page_written_copies_only_once`, protože testují odstraněné chování.

## Poznámky
- Guidelines: `/Users/msgre/projects/muzeum/krizky/docs/guidelines/python.md` (bez `from __future__ import annotations`, import z `krizky.plugin_helpers`) a `docs-sync.md`.
- Hookspec v core: `copy_plugin_assets(self, output_dir, config, config_dir)`, volá se jednou za build v `krizky/site.py`. Signaturu hookimpl dodrž přesně (pluggy páruje argumenty podle jmen).
- Záměrná změna chování: do výstupu se nově kopíruje i `icons.svg` a staré soubory v `output/krizky-share/` zmizí. `inject_body_end` dál vkládá sprite inline, to se nemění.
- `uv lock` potřebuje síť (zdroj core je git `https://github.com/msgre/krizky.git`). `scripts/verify` běží s `--frozen`, takže `uv.lock` musí být commitnutý aktualizovaný.
- `tests/test_macros.py` si skládá vlastní `ChoiceLoader` a na plugin hook nezávisí. Neměň ho.
- Mimo rozsah: CSS tokeny bez prefixu `--krizky-*`.

## Otázky
