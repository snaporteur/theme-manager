"""Géolocalisation via le service de localisation natif de Windows (winsdk).

Utilise Windows.Devices.Geolocation.Geolocator, le même mécanisme que les
applications natives comme Météo ou Cartes. Nécessite que le service de
localisation Windows soit activé et que l'accès pour les applications de
bureau soit autorisé (Paramètres > Confidentialité et sécurité > Position).
"""

import asyncio
from datetime import datetime, timedelta, timezone

from . import config as config_module

REFRESH_INTERVAL = timedelta(days=7)
REQUEST_TIMEOUT_SECONDS = 15


class LocationUnavailable(Exception):
    """Levée quand aucune position (fraîche ou en cache) n'a pu être obtenue."""


async def _fetch_from_windows_async():
    from winsdk.windows.devices.geolocation import Geolocator, PositionAccuracy

    locator = Geolocator()
    locator.desired_accuracy = PositionAccuracy.DEFAULT
    position = await asyncio.wait_for(
        locator.get_geoposition_async(), timeout=REQUEST_TIMEOUT_SECONDS
    )
    point = position.coordinate.point.position
    return point.latitude, point.longitude


def _fetch_from_windows():
    """Appel bloquant (à exécuter hors thread UI) vers Windows Location Services."""
    return asyncio.run(_fetch_from_windows_async())


def get_location(config=None, force_refresh=False):
    """Retourne (lat, lon, refreshed). Lève LocationUnavailable si rien n'est disponible."""
    own_config = config is None
    if own_config:
        config = config_module.load_config()

    cached = config["location"]
    cached_at_raw = cached.get("cached_at")
    is_fresh = False
    if cached_at_raw:
        cached_at = datetime.fromisoformat(cached_at_raw)
        is_fresh = (datetime.now(timezone.utc) - cached_at) < REFRESH_INTERVAL

    if not force_refresh and is_fresh and cached.get("lat") is not None:
        return cached["lat"], cached["lon"], False

    try:
        lat, lon = _fetch_from_windows()
    except Exception as exc:  # service désactivé, permission refusée, timeout, etc.
        if cached.get("lat") is not None:
            return cached["lat"], cached["lon"], False
        raise LocationUnavailable(
            "Impossible d'obtenir la position (service de localisation Windows "
            "désactivé ou accès refusé pour les applications de bureau)."
        ) from exc

    config["location"] = {
        "lat": lat,
        "lon": lon,
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }
    if own_config:
        config_module.save_config(config)

    return lat, lon, True
