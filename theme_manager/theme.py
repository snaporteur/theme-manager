"""Lecture/écriture du thème clair/sombre de Windows via le registre."""

import ctypes
import subprocess
import time
import winreg

_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002


def _get_theme_value(name):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _KEY_PATH) as key:
        value, _ = winreg.QueryValueEx(key, name)
    return "light" if value else "dark"


def get_apps_theme():
    """Retourne "light" ou "dark" selon AppsUseLightTheme."""
    return _get_theme_value("AppsUseLightTheme")


def get_system_theme():
    """Retourne "light" ou "dark" selon SystemUsesLightTheme (barre des tâches)."""
    return _get_theme_value("SystemUsesLightTheme")


def apply_profile(apps_theme, system_theme, restart_explorer=True):
    """Applique indépendamment le thème des apps et le thème système."""
    if apps_theme not in ("light", "dark") or system_theme not in ("light", "dark"):
        raise ValueError(f"thème invalide: apps={apps_theme!r} système={system_theme!r}")

    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(
            key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 1 if apps_theme == "light" else 0
        )
        winreg.SetValueEx(
            key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 1 if system_theme == "light" else 0
        )

    _broadcast_theme_change()

    if restart_explorer:
        restart_explorer_process()


def _broadcast_theme_change():
    """Notifie les apps déjà ouvertes (barre des tâches, Explorateur) du changement."""
    result = ctypes.c_long()
    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        "ImmersiveColorSet",
        SMTO_ABORTIFHUNG,
        1000,
        ctypes.byref(result),
    )


def restart_explorer_process():
    """Redémarre explorer.exe (évite des bugs d'affichage résiduels après un changement de thème).

    Ferme temporairement toutes les fenêtres de l'Explorateur de fichiers ouvertes.
    """
    subprocess.run(
        ["taskkill", "/F", "/IM", "explorer.exe"],
        check=False,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    time.sleep(1)
    subprocess.Popen(["explorer.exe"])
