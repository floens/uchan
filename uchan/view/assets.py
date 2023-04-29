import json
import os
from collections import namedtuple

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from uchan import config, logger

Asset = namedtuple("Asset", ["name", "type", "url"])

ThemeAsset = namedtuple("ThemeAsset", ["name", "title", "default", "asset"])


def setup_assets(app, watch_for_changes=False):
    if watch_for_changes:
        _start_watchdog_for_metafile(app)

    _set_assets_details(app)


def _start_watchdog_for_metafile(app):
    class Handler(FileSystemEventHandler):
        def on_any_event(self, event):
            if event.event_type == "modified":
                _set_assets_details(app)
                logger.debug("Assets metadata reloaded")

    observer = Observer()
    observer.schedule(Handler(), config.asset_build_meta_file)
    observer.start()


def _set_assets_details(app):
    with open(config.asset_build_meta_file, "r") as f:
        meta_file = json.load(f)

    assets = []
    themes = []
    for output_path, details in meta_file["output"].items():
        asset_type = details["type"]
        name = details["name"]
        filename = os.path.basename(output_path)
        url = _normalize_asset_url(config.asset_url + filename)

        asset = Asset(name, asset_type, url)
        assets.append(asset)

        if asset_type == "theme":
            themes.append(ThemeAsset(name, name, name == "uchan", asset))

    app.jinja_env.globals["assets"] = assets
    app.jinja_env.globals["assets_themes"] = themes


def _normalize_asset_url(asset_url: str):
    if asset_url.startswith(config.site_url):
        return asset_url[len(config.site_url) :]
    return asset_url
