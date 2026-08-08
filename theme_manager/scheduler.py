"""Boucle de fond qui vérifie périodiquement le créneau désiré et applique le profil associé."""

import threading
from contextlib import nullcontext
from datetime import datetime

from . import location, theme
from .suncalc import SunCalculator
from .timeutil import parse_hhmm

POLL_INTERVAL_SECONDS = 300  # 5 minutes

_FALLBACK_PROFILE = {"name": "?", "apps_theme": "dark", "system_theme": "dark"}


class Scheduler:
    def __init__(
        self, config, on_config_saved=None, on_theme_changed=None, on_notify=None, config_lock=None
    ):
        self._config = config
        self._on_config_saved = on_config_saved  # callable(config) -> persiste la config
        self._on_theme_changed = on_theme_changed  # callable(slot, profile_id)
        self._on_notify = on_notify  # callable(title, message)
        self._config_lock = config_lock or nullcontext()
        self._sun_calc = SunCalculator()
        self._stop_event = threading.Event()
        self._thread = None
        self._location_degraded_notified = False
        self._active_slot = None
        self._active_profile_id = None
        self.last_status = {}

    def start(self):
        self.tick()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def refresh_location(self):
        """Force la re-géolocalisation (déclenché depuis la fenêtre de paramètres)."""
        self.tick(force_location_refresh=True)

    def tick(self, force_location_refresh=False):
        now = datetime.now().astimezone()

        slot, status = self._compute_desired_slot(now, force_location_refresh)

        with self._config_lock:
            profile_id = self._config.get("schedule", {}).get(f"{slot}_profile")
            profile = self._config.get("profiles", {}).get(profile_id, _FALLBACK_PROFILE)

        status["slot"] = slot
        status["profile_id"] = profile_id
        status["profile_name"] = profile.get("name", profile_id)
        self.last_status = status

        apps_theme = profile["apps_theme"]
        system_theme = profile["system_theme"]
        drifted = (
            theme.get_apps_theme() != apps_theme or theme.get_system_theme() != system_theme
        )
        profile_changed = slot != self._active_slot or profile_id != self._active_profile_id

        if drifted:
            theme.apply_profile(
                apps_theme, system_theme, restart_explorer=self._config.get("restart_explorer", True)
            )

        if drifted or profile_changed:
            self._active_slot = slot
            self._active_profile_id = profile_id
            if self._on_theme_changed:
                self._on_theme_changed(slot, profile_id)

    def _run(self):
        while not self._stop_event.wait(POLL_INTERVAL_SECONDS):
            self.tick()

    def _compute_desired_slot(self, now, force_location_refresh):
        with self._config_lock:
            mode = self._config.get("mode", "sun")
            fixed_hours = dict(self._config.get("fixed_hours", {}))

        if mode == "fixed":
            return self._desired_slot_from_fixed_hours(now, fixed_hours), {
                "mode": "fixed",
                "fixed_hours": fixed_hours,
            }

        try:
            lat, lon, refreshed = location.get_location(
                self._config, force_refresh=force_location_refresh
            )
        except location.LocationUnavailable as exc:
            if not self._location_degraded_notified and self._on_notify:
                self._on_notify(
                    "Position indisponible",
                    "Bascule sur des heures fixes (07:00 / 20:00) : active le service de "
                    "localisation Windows pour un calcul basé sur le soleil.",
                )
            self._location_degraded_notified = True
            return self._desired_slot_from_fixed_hours(now, fixed_hours), {
                "mode": "sun-degraded",
                "error": str(exc),
            }

        self._location_degraded_notified = False
        if refreshed and self._on_config_saved:
            self._on_config_saved(self._config)

        sunrise, sunset = self._sun_calc.get_sun_times(lat, lon, now)
        slot = "day" if sunrise <= now < sunset else "night"
        return slot, {
            "mode": "sun",
            "lat": lat,
            "lon": lon,
            "sunrise": sunrise,
            "sunset": sunset,
        }

    def _desired_slot_from_fixed_hours(self, now, fixed_hours):
        day_h, day_m = parse_hhmm(fixed_hours.get("day_start", "07:00"))
        night_h, night_m = parse_hhmm(fixed_hours.get("night_start", "20:00"))

        day_start = now.replace(hour=day_h, minute=day_m, second=0, microsecond=0)
        night_start = now.replace(hour=night_h, minute=night_m, second=0, microsecond=0)

        if day_start <= night_start:
            return "day" if day_start <= now < night_start else "night"
        return "night" if night_start <= now < day_start else "day"
