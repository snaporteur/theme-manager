"""Theme Manager — icône barre système + fenêtre de paramètres pour la bascule auto clair/sombre."""

import copy
import threading

import pystray

from theme_manager import autostart
from theme_manager import config as config_module
from theme_manager import icon as icon_module
from theme_manager import settings_window
from theme_manager import theme
from theme_manager.scheduler import Scheduler

_config = config_module.load_config()
_config_lock = threading.Lock()


def _save_config(cfg=None):
    with _config_lock:
        config_module.save_config(cfg if cfg is not None else _config)


def _on_theme_changed(slot, profile_id):
    tray_icon.icon = icon_module.create_icon(slot)
    tray_icon.update_menu()


def _on_notify(title, message):
    tray_icon.notify(message, title)


scheduler = Scheduler(
    _config,
    on_config_saved=_save_config,
    on_theme_changed=_on_theme_changed,
    on_notify=_on_notify,
    config_lock=_config_lock,
)


def _status_text(item=None):
    status = scheduler.last_status
    profile_name = status.get("profile_name", "…")
    apps_label = "Clair" if theme.get_apps_theme() == "light" else "Sombre"
    system_label = "Clair" if theme.get_system_theme() == "light" else "Sombre"
    base = f"{profile_name} — apps {apps_label} / système {system_label}"

    mode = status.get("mode")
    if mode == "sun":
        sunrise = status.get("sunrise")
        sunset = status.get("sunset")
        if sunrise is not None and sunset is not None:
            return f"{base} (lever {sunrise.strftime('%H:%M')} / coucher {sunset.strftime('%H:%M')})"
        return f"{base} (calcul en cours…)"
    if mode == "sun-degraded":
        return f"{base} — position indisponible, repli heures fixes"
    if mode == "fixed":
        fixed = status.get("fixed_hours", _config["fixed_hours"])
        return f"{base} (heures fixes {fixed['day_start']} / {fixed['night_start']})"
    return f"{base} — initialisation…"


def _handle_settings_save(new_config):
    with _config_lock:
        autostart_changed = new_config.get("autostart") != _config.get("autostart")
        _config.clear()
        _config.update(new_config)
        config_module.save_config(_config)
    if autostart_changed:
        autostart.set_enabled(_config["autostart"])
    scheduler.tick()
    tray_icon.update_menu()


def _handle_apply_now(apps_theme, system_theme, restart_explorer):
    theme.apply_profile(apps_theme, system_theme, restart_explorer=restart_explorer)


def _handle_refresh_location():
    scheduler.refresh_location()
    with _config_lock:
        return dict(_config.get("location", {}))


def _open_settings(icon, item):
    with _config_lock:
        snapshot = copy.deepcopy(_config)
    opened = settings_window.open_settings_window(
        snapshot,
        on_save=_handle_settings_save,
        on_apply_now=_handle_apply_now,
        on_refresh_location=_handle_refresh_location,
    )
    if not opened:
        tray_icon.notify("Les paramètres sont déjà ouverts.", "Theme Manager")


def _quit(icon, item):
    scheduler.stop()
    icon.stop()


def _build_menu():
    return pystray.Menu(
        pystray.MenuItem(_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Ouvrir les paramètres", _open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quitter", _quit),
    )


tray_icon = pystray.Icon(
    "ThemeManager",
    icon_module.create_icon("day"),
    "Theme Manager",
    menu=_build_menu(),
)


def _setup(icon):
    icon.visible = True
    scheduler.start()


def main():
    tray_icon.run(setup=_setup)


if __name__ == "__main__":
    main()
