"""Chargement/sauvegarde de la configuration utilisateur (config.json)."""

import json
import os
import uuid

CONFIG_DIR = os.path.join(os.environ["APPDATA"], "ThemeManager")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

CONFIG_VERSION = 2

PROFILE_TEMPLATE = {"name": "", "apps_theme": "light", "system_theme": "light"}

DEFAULT_CONFIG = {
    "version": CONFIG_VERSION,
    "mode": "sun",  # "sun" ou "fixed"
    "location": {"lat": None, "lon": None, "cached_at": None},
    "fixed_hours": {"day_start": "07:00", "night_start": "20:00"},
    "profiles": {
        "day": {"name": "Jour", "apps_theme": "light", "system_theme": "light"},
        "night": {"name": "Nuit", "apps_theme": "dark", "system_theme": "dark"},
    },
    "schedule": {"day_profile": "day", "night_profile": "night"},
    "restart_explorer": False,
    "autostart": False,
}

# Sections fusionnées récursivement avec les valeurs par défaut pour compléter
# les clés manquantes. "profiles" est traité à part (liste ouverte gérée par
# l'utilisateur, cf. _merge_profiles).
_DEEP_MERGE_KEYS = ("location", "fixed_hours", "schedule")


def new_profile_id():
    return uuid.uuid4().hex[:8]


def _deep_merge(default, override):
    merged = dict(default)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _merge_profiles(profiles):
    if not isinstance(profiles, dict) or not profiles:
        return json.loads(json.dumps(DEFAULT_CONFIG["profiles"]))
    return {
        profile_id: _deep_merge(PROFILE_TEMPLATE, profile)
        for profile_id, profile in profiles.items()
    }


def _migrate(raw):
    fixed_hours = raw.get("fixed_hours")
    if isinstance(fixed_hours, dict) and (
        "light_start" in fixed_hours or "dark_start" in fixed_hours
    ):
        if "day_start" not in fixed_hours and "light_start" in fixed_hours:
            fixed_hours["day_start"] = fixed_hours.pop("light_start")
        if "night_start" not in fixed_hours and "dark_start" in fixed_hours:
            fixed_hours["night_start"] = fixed_hours.pop("dark_start")

    profiles = raw.get("profiles")
    if isinstance(profiles, dict):
        if "day" in profiles and "name" not in profiles["day"]:
            profiles["day"]["name"] = "Jour"
        if "night" in profiles and "name" not in profiles["night"]:
            profiles["night"]["name"] = "Nuit"

    if "schedule" not in raw:
        raw["schedule"] = {"day_profile": "day", "night_profile": "night"}

    return raw


def _merge_defaults(raw):
    raw = _migrate(raw)
    merged = dict(DEFAULT_CONFIG)
    for key in _DEEP_MERGE_KEYS:
        merged[key] = _deep_merge(DEFAULT_CONFIG[key], raw.get(key, {}))
    merged["profiles"] = _merge_profiles(raw.get("profiles"))
    for key, value in raw.items():
        if key not in _DEEP_MERGE_KEYS and key != "profiles":
            merged[key] = value
    merged["version"] = CONFIG_VERSION
    return merged


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return _merge_defaults(json.load(f))
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
