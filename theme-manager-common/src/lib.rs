use std::{fs, path::{PathBuf}};

use chrono::NaiveTime;
use directories::ProjectDirs;
use ron::ser::{PrettyConfig, to_string_pretty};
use serde::{Deserialize, Serialize};

#[derive(Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ThemeColor {
    Light,
    Dark,
}

#[derive(Serialize, Deserialize)]
pub struct ThemeTime {
    pub enabled: bool,

    pub start: NaiveTime,
    pub end: NaiveTime,

    pub apps: ThemeColor,
    pub system: ThemeColor,
}

impl ThemeTime {
    pub fn is_active(&self, now: NaiveTime) -> bool {
        if self.start <= self.end {
            now >= self.start && now < self.end
        } else {
            now >= self.start || now < self.end
        }
    }
}

#[derive(Serialize, Deserialize)]
pub struct Config {
    pub theme_times: Vec<ThemeTime>,
    pub autostart: bool,
}

pub fn create_default_config() -> Config {
    Config {
        theme_times: vec![
            ThemeTime {
                enabled: true,
                start: NaiveTime::from_hms_opt(7, 0, 0).unwrap(),
                end: NaiveTime::from_hms_opt(20, 0, 0).unwrap(),
                apps: ThemeColor::Light,
                system: ThemeColor::Light,
            },
            ThemeTime {
                enabled: true,
                start: NaiveTime::from_hms_opt(20, 0, 0).unwrap(),
                end: NaiveTime::from_hms_opt(7, 0, 0).unwrap(),
                apps: ThemeColor::Dark,
                system: ThemeColor::Dark,
            }
        ],
        autostart: false,
    }
}

pub fn get_config_folder_path() -> Result<PathBuf, Box<dyn std::error::Error>> {
    let dirs = ProjectDirs::from("fr", "snaporteur", "ThemeManager")
        .ok_or("Unable to find config directories.")?;

    Ok(dirs.config_dir().to_path_buf())
}

pub fn get_config_path() -> Result<PathBuf, Box<dyn std::error::Error>> {
    Ok(get_config_folder_path()?.join("config.ron"))
}

pub fn load_or_save_config() -> Result<Config, Box<dyn std::error::Error>> {
    let file_path = get_config_path()?;

    if file_path.exists() {
        println!("Reading existing config.");
        Ok(ron::from_str(&fs::read_to_string(file_path)?.to_string())?)
    } else {
        println!("Create default config file.");
        fs::create_dir_all(get_config_folder_path()?)?;
        let config = create_default_config();
        fs::write(file_path, to_string_pretty(&config, PrettyConfig::new())?)?;
        Ok(config)
    }
}

pub fn save_config(conf: &Config) -> Result<(), Box<dyn std::error::Error>> {
    fs::create_dir_all(get_config_folder_path()?)?;
    fs::write(get_config_path()?, to_string_pretty(&conf, PrettyConfig::new())?)?;
    Ok(())
}