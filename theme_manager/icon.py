"""Génère dynamiquement l'icône de la barre système (soleil clair / lune sombre)."""

import math

from PIL import Image, ImageDraw

SIZE = 64


def create_icon(slot):
    """Retourne une image PIL représentant le créneau horaire actif ("day" ou "night")."""
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if slot == "day":
        _draw_sun(draw)
    else:
        _draw_moon(draw)

    return image


def _draw_sun(draw):
    center = SIZE // 2
    radius = SIZE // 5
    color = (255, 179, 0, 255)

    for i in range(8):
        angle = math.pi / 4 * i
        x1 = center + math.cos(angle) * (radius + 4)
        y1 = center + math.sin(angle) * (radius + 4)
        x2 = center + math.cos(angle) * (radius + 14)
        y2 = center + math.sin(angle) * (radius + 14)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=4)

    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=color,
    )


def _draw_moon(draw):
    center = SIZE // 2
    radius = SIZE // 3
    color = (222, 226, 235, 255)

    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=color,
    )

    # Le croissant est obtenu en effaçant (mise à transparent) un disque décalé.
    shadow_offset = radius // 2
    draw.ellipse(
        [
            center - radius + shadow_offset,
            center - radius - shadow_offset // 2,
            center + radius + shadow_offset,
            center + radius - shadow_offset // 2,
        ],
        fill=(0, 0, 0, 0),
    )
