#![windows_subsystem = "windows"]

mod tray;
mod theme;

use std::{fs, time::Duration};
use chrono::Local;
use theme_manager_common::{get_config_folder_path, load_or_save_config, Config, ThemeColor};
use tray::{Tray, ThemeMode};
use theme::Theme;

/// Couleurs (apps, système) à appliquer selon le mode du tray et la config.
fn target_colors(mode: ThemeMode, config: &Config) -> Option<(ThemeColor, ThemeColor)> {
    match mode {
        ThemeMode::ForceLight => Some((ThemeColor::Light, ThemeColor::Light)),
        ThemeMode::ForceDark => Some((ThemeColor::Dark, ThemeColor::Dark)),
        ThemeMode::Auto => {
            let now = Local::now().time();
            config
                .theme_times
                .iter()
                .find(|t| t.enabled && t.is_active(now))
                .map(|t| (t.apps.clone(), t.system.clone()))
        }
    }
}

fn main() {
    let mut tray: Tray = Tray::new();

    let mut theme: Theme = Theme::new();
    let mut applied: Option<(ThemeColor, ThemeColor)> = None;

    let reloadpath = get_config_folder_path().unwrap().join("needreload");
    let mut config = load_or_save_config().expect("Failed to get config.");

    // Vérifie la plage active environ toutes les secondes, tout en traitant
    // les clics du tray plus souvent pour que le menu reste réactif.
    let tick = Duration::from_millis(100);
    let check_every = 10;
    let mut ticks = check_every;
    let mut last_mode = tray.mode();

    while tray.process_until_close() {
        let mode = tray.mode();
        if mode != last_mode {
            last_mode = mode;
            ticks = check_every;
        }

        if ticks >= check_every {
            ticks = 0;

            if reloadpath.exists() {
                match load_or_save_config() {
                    Ok(c) => {
                        config = c;
                        let _ = fs::remove_file(&reloadpath);
                        println!("Config reloaded.");
                    },
                    Err(_) => println!("Error reloading config.")
                }
            }

            if let Some(target) = target_colors(mode, &config) {
                if applied.as_ref() != Some(&target) {
                    println!("Changing theme.");
                    theme.set_apps_color(target.0.clone());
                    theme.set_system_color(target.1.clone());
                    theme.apply();
                    applied = Some(target);
                }
            }
        }

        ticks += 1;
        std::thread::sleep(tick);
    }
}
