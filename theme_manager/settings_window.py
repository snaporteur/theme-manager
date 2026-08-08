"""Fenêtre de paramètres (tkinter) : mode, position, profils, planification, options."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from . import config as config_module
from .timeutil import parse_hhmm

_lock = threading.Lock()
_window_open = False

_THEME_LABELS = {"light": "Clair", "dark": "Sombre"}
_LABEL_TO_THEME = {v: k for k, v in _THEME_LABELS.items()}


def open_settings_window(config_snapshot, *, on_save, on_apply_now, on_refresh_location):
    """Ouvre la fenêtre de paramètres dans un thread dédié. Retourne False si déjà ouverte."""
    global _window_open
    with _lock:
        if _window_open:
            return False
        _window_open = True

    thread = threading.Thread(
        target=_run,
        args=(config_snapshot, on_save, on_apply_now, on_refresh_location),
        daemon=True,
    )
    thread.start()
    return True


def _run(config, on_save, on_apply_now, on_refresh_location):
    global _window_open
    try:
        _SettingsWindow(config, on_save, on_apply_now, on_refresh_location).root.mainloop()
    finally:
        with _lock:
            _window_open = False


def _format_location(location):
    lat, lon = location.get("lat"), location.get("lon")
    if lat is None or lon is None:
        return "Aucune position enregistrée."
    cached_at = location.get("cached_at", "")
    return f"Lat {lat:.4f}, Lon {lon:.4f} (mis à jour : {cached_at[:19].replace('T', ' ')})"


def _format_profile_line(profile):
    apps = _THEME_LABELS.get(profile.get("apps_theme"), "?")
    system = _THEME_LABELS.get(profile.get("system_theme"), "?")
    return f"{profile.get('name', '?')} — Apps : {apps}, Système : {system}"


class _SettingsWindow:
    def __init__(self, config, on_save, on_apply_now, on_refresh_location):
        self._config = config
        self._on_save = on_save
        self._on_apply_now = on_apply_now
        self._on_refresh_location = on_refresh_location

        self._profile_order = []  # index de la Listbox -> id de profil
        self._current_edit_id = None

        self.root = tk.Tk()
        self.root.title("Theme Manager — Paramètres")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        self._build_ui()
        self._refresh_profile_listbox()
        self._refresh_schedule_combos()

    # ----- Construction de l'interface -----------------------------------

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        mode_frame = ttk.LabelFrame(self.root, text="Mode")
        mode_frame.grid(row=0, column=0, sticky="ew", **pad)
        self.mode_var = tk.StringVar(value=self._config.get("mode", "sun"))
        ttk.Radiobutton(
            mode_frame, text="Automatique (lever/coucher du soleil)",
            variable=self.mode_var, value="sun", command=self._update_mode_state,
        ).pack(anchor="w")
        ttk.Radiobutton(
            mode_frame, text="Heures fixes",
            variable=self.mode_var, value="fixed", command=self._update_mode_state,
        ).pack(anchor="w")

        pos_frame = ttk.LabelFrame(self.root, text="Position (mode automatique)")
        pos_frame.grid(row=1, column=0, sticky="ew", **pad)
        self.location_var = tk.StringVar(value=_format_location(self._config.get("location", {})))
        ttk.Label(pos_frame, textvariable=self.location_var, wraplength=380).pack(
            anchor="w", fill="x"
        )
        self._refresh_location_btn = ttk.Button(
            pos_frame, text="Actualiser la position", command=self._on_refresh_location_clicked
        )
        self._refresh_location_btn.pack(anchor="w", pady=(4, 0))

        hours_frame = ttk.LabelFrame(self.root, text="Heures fixes")
        hours_frame.grid(row=2, column=0, sticky="ew", **pad)
        fixed_hours = self._config.get("fixed_hours", {})
        self.day_start_var = tk.StringVar(value=fixed_hours.get("day_start", "07:00"))
        self.night_start_var = tk.StringVar(value=fixed_hours.get("night_start", "20:00"))
        row = ttk.Frame(hours_frame)
        row.pack(anchor="w", fill="x")
        ttk.Label(row, text="Début du jour (HH:MM)").grid(row=0, column=0, sticky="w")
        self._day_start_entry = ttk.Entry(row, textvariable=self.day_start_var, width=8)
        self._day_start_entry.grid(row=0, column=1, padx=(8, 0))
        ttk.Label(row, text="Début de la nuit (HH:MM)").grid(row=1, column=0, sticky="w")
        self._night_start_entry = ttk.Entry(row, textvariable=self.night_start_var, width=8)
        self._night_start_entry.grid(row=1, column=1, padx=(8, 0))

        profiles_frame = ttk.LabelFrame(self.root, text="Profils")
        profiles_frame.grid(row=3, column=0, sticky="ew", **pad)

        list_row = ttk.Frame(profiles_frame)
        list_row.pack(fill="x")
        self.profile_listbox = tk.Listbox(list_row, height=5, width=48, exportselection=False)
        self.profile_listbox.pack(side="left", fill="x", expand=True)
        self.profile_listbox.bind("<<ListboxSelect>>", self._on_profile_select)

        btn_col = ttk.Frame(list_row)
        btn_col.pack(side="left", padx=(6, 0))
        ttk.Button(btn_col, text="Ajouter", command=self._add_profile).pack(fill="x")
        ttk.Button(btn_col, text="Supprimer", command=self._delete_profile).pack(fill="x", pady=(4, 0))

        edit_row = ttk.Frame(profiles_frame)
        edit_row.pack(fill="x", pady=(8, 0))
        ttk.Label(edit_row, text="Nom").grid(row=0, column=0, sticky="w")
        self.profile_name_var = tk.StringVar()
        ttk.Entry(edit_row, textvariable=self.profile_name_var, width=28).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        ttk.Label(edit_row, text="Apps").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.profile_apps_var = tk.StringVar(value="Clair")
        apps_row = ttk.Frame(edit_row)
        apps_row.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
        ttk.Radiobutton(apps_row, text="Clair", variable=self.profile_apps_var, value="Clair").pack(side="left")
        ttk.Radiobutton(apps_row, text="Sombre", variable=self.profile_apps_var, value="Sombre").pack(side="left")

        ttk.Label(edit_row, text="Système (barre des tâches)").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.profile_system_var = tk.StringVar(value="Clair")
        system_row = ttk.Frame(edit_row)
        system_row.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
        ttk.Radiobutton(system_row, text="Clair", variable=self.profile_system_var, value="Clair").pack(side="left")
        ttk.Radiobutton(system_row, text="Sombre", variable=self.profile_system_var, value="Sombre").pack(side="left")

        for var in (self.profile_name_var, self.profile_apps_var, self.profile_system_var):
            var.trace_add("write", self._on_profile_edit_changed)

        schedule_frame = ttk.LabelFrame(self.root, text="Planification")
        schedule_frame.grid(row=4, column=0, sticky="ew", **pad)
        ttk.Label(schedule_frame, text="Profil du jour").grid(row=0, column=0, sticky="w")
        self.day_profile_var = tk.StringVar()
        self.day_profile_combo = ttk.Combobox(
            schedule_frame, textvariable=self.day_profile_var, state="readonly", width=30
        )
        self.day_profile_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(schedule_frame, text="Profil de la nuit").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.night_profile_var = tk.StringVar()
        self.night_profile_combo = ttk.Combobox(
            schedule_frame, textvariable=self.night_profile_var, state="readonly", width=30
        )
        self.night_profile_combo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))

        options_frame = ttk.LabelFrame(self.root, text="Options")
        options_frame.grid(row=5, column=0, sticky="ew", **pad)
        self.autostart_var = tk.BooleanVar(value=self._config.get("autostart", False))
        ttk.Checkbutton(
            options_frame, text="Démarrer avec Windows", variable=self.autostart_var
        ).pack(anchor="w")
        self.restart_explorer_var = tk.BooleanVar(value=self._config.get("restart_explorer", True))
        ttk.Checkbutton(
            options_frame,
            text="Redémarrer l'Explorateur Windows après un changement de thème",
            variable=self.restart_explorer_var,
        ).pack(anchor="w")
        ttk.Label(
            options_frame,
            text=(
                "Recommandé pour éviter des bugs d'affichage après un changement de thème.\n"
                "Ferme temporairement toutes les fenêtres de l'Explorateur de fichiers ouvertes."
            ),
            foreground="#666666",
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        button_row = ttk.Frame(self.root)
        button_row.grid(row=6, column=0, sticky="ew", padx=8, pady=(4, 8))
        ttk.Button(button_row, text="Appliquer maintenant", command=self._apply_now).pack(side="left")
        ttk.Button(button_row, text="Enregistrer", command=self._save).pack(side="right")
        ttk.Button(button_row, text="Fermer", command=self.root.destroy).pack(side="right", padx=(0, 6))

        self._update_mode_state()

    def _update_mode_state(self):
        fixed = self.mode_var.get() == "fixed"
        state = "normal" if fixed else "disabled"
        self._day_start_entry.config(state=state)
        self._night_start_entry.config(state=state)
        self._refresh_location_btn.config(state="disabled" if fixed else "normal")

    # ----- Profils ---------------------------------------------------------

    def _refresh_profile_listbox(self, select_id=None):
        self.profile_listbox.delete(0, tk.END)
        self._profile_order = list(self._config["profiles"].keys())
        for profile_id in self._profile_order:
            self.profile_listbox.insert(tk.END, _format_profile_line(self._config["profiles"][profile_id]))

        if select_id and select_id in self._profile_order:
            index = self._profile_order.index(select_id)
            self.profile_listbox.selection_set(index)
            self._load_profile_into_editor(select_id)
        elif self._profile_order:
            self.profile_listbox.selection_set(0)
            self._load_profile_into_editor(self._profile_order[0])
        else:
            self._current_edit_id = None

    def _on_profile_select(self, _event):
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        profile_id = self._profile_order[selection[0]]
        if profile_id == self._current_edit_id:
            return
        self._load_profile_into_editor(profile_id)

    def _load_profile_into_editor(self, profile_id):
        profile = self._config["profiles"][profile_id]
        self._current_edit_id = None  # évite de ré-écrire pendant le chargement
        self.profile_name_var.set(profile.get("name", ""))
        self.profile_apps_var.set(_THEME_LABELS.get(profile.get("apps_theme", "light"), "Clair"))
        self.profile_system_var.set(_THEME_LABELS.get(profile.get("system_theme", "light"), "Clair"))
        self._current_edit_id = profile_id

    def _on_profile_edit_changed(self, *_args):
        if not self._current_edit_id:
            return
        profile = self._config["profiles"][self._current_edit_id]
        profile["name"] = self.profile_name_var.get().strip() or "Sans nom"
        profile["apps_theme"] = _LABEL_TO_THEME.get(self.profile_apps_var.get(), "light")
        profile["system_theme"] = _LABEL_TO_THEME.get(self.profile_system_var.get(), "light")

        selection = self.profile_listbox.curselection()
        if selection:
            self.profile_listbox.delete(selection[0])
            self.profile_listbox.insert(selection[0], _format_profile_line(profile))
            self.profile_listbox.selection_set(selection[0])
        self._refresh_schedule_combos()

    def _add_profile(self):
        new_id = config_module.new_profile_id()
        self._config["profiles"][new_id] = {
            "name": "Nouveau profil",
            "apps_theme": "light",
            "system_theme": "light",
        }
        self._refresh_profile_listbox(select_id=new_id)
        self._refresh_schedule_combos()

    def _delete_profile(self):
        if not self._current_edit_id:
            return
        profile_id = self._current_edit_id
        schedule = self._config.get("schedule", {})
        if profile_id in (schedule.get("day_profile"), schedule.get("night_profile")):
            messagebox.showerror(
                "Suppression impossible",
                "Ce profil est utilisé par la planification (jour ou nuit). "
                "Assigne un autre profil à ce créneau avant de le supprimer.",
                parent=self.root,
            )
            return
        if len(self._config["profiles"]) <= 1:
            messagebox.showerror(
                "Suppression impossible", "Il doit rester au moins un profil.", parent=self.root
            )
            return
        del self._config["profiles"][profile_id]
        self._current_edit_id = None
        self._refresh_profile_listbox()
        self._refresh_schedule_combos()

    # ----- Planification -----------------------------------------------

    def _refresh_schedule_combos(self):
        names = [self._config["profiles"][pid]["name"] for pid in self._profile_order]
        self.day_profile_combo["values"] = names
        self.night_profile_combo["values"] = names

        schedule = self._config.get("schedule", {})
        day_id = schedule.get("day_profile")
        night_id = schedule.get("night_profile")
        if day_id in self._config["profiles"]:
            self.day_profile_var.set(self._config["profiles"][day_id]["name"])
        elif names:
            self.day_profile_var.set(names[0])
        if night_id in self._config["profiles"]:
            self.night_profile_var.set(self._config["profiles"][night_id]["name"])
        elif names:
            self.night_profile_var.set(names[0])

    def _resolve_profile_id_by_name(self, name):
        for profile_id in self._profile_order:
            if self._config["profiles"][profile_id]["name"] == name:
                return profile_id
        return self._profile_order[0] if self._profile_order else None

    # ----- Position -------------------------------------------------------

    def _on_refresh_location_clicked(self):
        self._refresh_location_btn.config(state="disabled")
        self.location_var.set("Actualisation en cours…")

        def worker():
            try:
                updated_location = self._on_refresh_location()
                message = _format_location(updated_location)
                self._config["location"] = updated_location
            except Exception as exc:  # affichage d'erreur, pas de crash du thread
                message = f"Échec de la géolocalisation : {exc}"
            self.root.after(0, lambda: self._on_location_refreshed(message))

        threading.Thread(target=worker, daemon=True).start()

    def _on_location_refreshed(self, message):
        self.location_var.set(message)
        self._refresh_location_btn.config(state="normal")

    # ----- Actions bas de fenêtre ------------------------------------------

    def _apply_now(self):
        if not self._current_edit_id:
            messagebox.showinfo("Aucun profil sélectionné", "Sélectionne un profil à appliquer.", parent=self.root)
            return
        profile = self._config["profiles"][self._current_edit_id]
        self._on_apply_now(profile["apps_theme"], profile["system_theme"], self.restart_explorer_var.get())

    def _save(self):
        try:
            parse_hhmm(self.day_start_var.get().strip())
            parse_hhmm(self.night_start_var.get().strip())
        except ValueError:
            messagebox.showerror(
                "Heure invalide", "Les heures doivent être au format HH:MM (ex : 07:00).", parent=self.root
            )
            return

        self._config["mode"] = self.mode_var.get()
        self._config["fixed_hours"] = {
            "day_start": self.day_start_var.get().strip(),
            "night_start": self.night_start_var.get().strip(),
        }
        self._config["schedule"] = {
            "day_profile": self._resolve_profile_id_by_name(self.day_profile_var.get()),
            "night_profile": self._resolve_profile_id_by_name(self.night_profile_var.get()),
        }
        self._config["autostart"] = self.autostart_var.get()
        self._config["restart_explorer"] = self.restart_explorer_var.get()

        self._on_save(self._config)
        self.root.destroy()
