"""Calcul des heures de lever/coucher du soleil (via astral), avec cache journalier."""

from datetime import datetime

from astral import Observer
from astral.sun import sun


class SunCalculator:
    """Recalcule sunrise/sunset une seule fois par jour et par position."""

    def __init__(self):
        self._cache_key = None
        self._sunrise = None
        self._sunset = None

    def get_sun_times(self, lat, lon, now=None):
        """Retourne (sunrise, sunset) en datetime locaux avec fuseau horaire, pour aujourd'hui."""
        now = now or datetime.now().astimezone()
        today = now.date()
        cache_key = (round(lat, 3), round(lon, 3), today)

        if cache_key != self._cache_key:
            observer = Observer(latitude=lat, longitude=lon)
            times = sun(observer, date=today, tzinfo=now.tzinfo)
            self._sunrise = times["sunrise"]
            self._sunset = times["sunset"]
            self._cache_key = cache_key

        return self._sunrise, self._sunset
