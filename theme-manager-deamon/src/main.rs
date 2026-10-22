#![windows_subsystem = "windows"]

mod tray;
mod theme;

use std::fs;
use chrono::Local;
use theme_manager_common::{get_config_folder_path, load_or_save_config};
use tray::Tray;
use theme::Theme;

fn main() {
    let tray: Tray = Tray::new();

    let mut theme: Theme = Theme::new();
    let mut current_theme: usize = 0;

    let reloadpath = get_config_folder_path().unwrap().join("needreload");
    let mut config = load_or_save_config().expect("Failed to get config.");

    while tray.process_until_close() {
        let now = Local::now().time();

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

        for (index, theme_time) in config.theme_times.iter().enumerate() {
            if !theme_time.enabled {continue;}

            if theme_time.is_active(now) && current_theme != index {
                println!("Changing theme.");
                theme.set_apps_color(theme_time.apps.clone());
                theme.set_system_color(theme_time.system.clone());
                theme.apply();
                current_theme = index;
                break;
            }

            std::thread::sleep(std::time::Duration::from_millis(1000));
        }
    }
}
