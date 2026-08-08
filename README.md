# Theme Manager

Bascule automatique du thème Windows (clair/sombre) en fonction du lever/coucher du
soleil — comme le mode "Automatique" de macOS. Tourne en arrière-plan avec une icône
dans la barre système ; toute la configuration se fait dans une fenêtre de paramètres.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

Une icône (soleil le jour, lune la nuit) apparaît dans la barre système. Clic droit
dessus pour ouvrir le menu :

- **Statut** — profil actif et thèmes actuels (apps / système).
- **Ouvrir les paramètres** — ouvre la fenêtre de configuration.
- **Quitter**.

## Fenêtre de paramètres

- **Mode** — Automatique (soleil) ou Heures fixes.
- **Position** — position utilisée pour le calcul lever/coucher (via le service de
  localisation Windows), avec un bouton pour l'actualiser.
- **Heures fixes** — heure de début du jour et de la nuit, utilisées si le mode
  "Heures fixes" est actif.
- **Profils** — liste librement gérable (Ajouter / Supprimer) de profils nommés.
  Chaque profil définit **indépendamment** le thème des applications et le thème du
  système (barre des tâches, menu Démarrer) — par exemple pour garder la barre des
  tâches toujours en noir même avec des applications en thème clair.
- **Planification** — assigne un profil de la liste au créneau "jour" et un (ou le
  même) au créneau "nuit".
- **Options** — démarrage avec Windows, et redémarrage automatique de l'Explorateur
  Windows après un changement de thème (recommandé pour éviter des bugs d'affichage ;
  ferme temporairement les fenêtres de l'Explorateur de fichiers ouvertes).
- **Appliquer maintenant** — applique immédiatement le profil sélectionné, sans
  enregistrer (utile pour prévisualiser). **Enregistrer** persiste la configuration.

## Géolocalisation

Le mode "Automatique (soleil)" utilise le **service de localisation natif de
Windows** (le même que l'app Météo), pas de service web tiers. Pour qu'il fonctionne :

1. Ouvrir **Paramètres > Confidentialité et sécurité > Position**.
2. Activer **Service de localisation**.
3. Vérifier que **Laisser les applications de bureau accéder à votre position** est
   activé.

Si la position n'est pas disponible (service désactivé, permission refusée), l'outil
bascule automatiquement sur des heures fixes (07:00 / 20:00 par défaut) et affiche une
notification tant que le problème n'est pas résolu.

## Configuration

Le fichier `config.json` se trouve dans `%APPDATA%\ThemeManager\config.json` :

```json
{
  "version": 2,
  "mode": "sun",
  "location": {"lat": null, "lon": null, "cached_at": null},
  "fixed_hours": {"day_start": "07:00", "night_start": "20:00"},
  "profiles": {
    "day": {"name": "Jour", "apps_theme": "light", "system_theme": "light"},
    "night": {"name": "Nuit", "apps_theme": "dark", "system_theme": "dark"}
  },
  "schedule": {"day_profile": "day", "night_profile": "night"},
  "restart_explorer": true,
  "autostart": false
}
```

Ce fichier n'a normalement pas besoin d'être édité à la main — tout est géré depuis la
fenêtre de paramètres.

## Démarrage automatique avec Windows

Activable directement depuis la fenêtre de paramètres ("Démarrer avec Windows"). Cela
ajoute une entrée dans `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` qui lance
`pythonw.exe main.py` (sans fenêtre console) à l'ouverture de session.
