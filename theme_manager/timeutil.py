"""Petits utilitaires de parsing d'heures partagés par le scheduler et la fenêtre de paramètres."""


def parse_hhmm(value):
    """Convertit "HH:MM" en (heure, minute). Lève ValueError si le format est invalide."""
    hour_str, minute_str = value.split(":")
    hour, minute = int(hour_str), int(minute_str)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"heure invalide: {value!r}")
    return hour, minute
