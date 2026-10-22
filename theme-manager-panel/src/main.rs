#![windows_subsystem = "windows"]

use std::fs;
use chrono::NaiveTime;
use eframe::egui::{self, Color32, Frame, Stroke};
use theme_manager_common::{
    ThemeColor::{self}, ThemeTime, get_config_folder_path, load_or_save_config, save_config,
};

fn move_item<T>(vec: &mut Vec<T>, from: usize, to: usize) {
    if from >= vec.len() || to >= vec.len() || from == to {
        return;
    }

    let item = vec.remove(from);
    vec.insert(to, item);
}

struct AppState {
    theme_index: usize,
    enabled: bool,
    start: String,
    end: String,
    apps_light: bool,
    system_light: bool,
}

impl AppState {
    fn new() -> Self {
        AppState {
            theme_index: 0,
            enabled: true,
            start: String::new(),
            end: String::new(),
            apps_light: true,
            system_light: true,
        }
    }
}

fn main() -> eframe::Result {
    let mut app_state = AppState::new();
    let mut config = load_or_save_config().unwrap();

    app_state.start = config.theme_times[0].start.to_string();
    app_state.end = config.theme_times[0].end.to_string();

    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([320.0, 440.0]),
        ..Default::default()
    };

    eframe::run_ui_native("ThemeManager Panel", options, move |ui, _frame| {
        egui::CentralPanel::default().show(ui, |ui| {
            ui.heading("ThemeManager Panel");

            Frame::new()
                .stroke(Stroke::new(1.0, Color32::BLACK))
                .show(ui, |ui| {
                    ui.set_width(ui.available_width());
                    ui.set_min_height(170.0);

                    for (index, theme_time) in config.theme_times.iter().enumerate() {
                        ui.horizontal(|ui| {
                            if ui
                                .button(format!(
                                    "ThemeTime {}: {}-{}",
                                    index, theme_time.start, theme_time.end
                                ))
                                .clicked()
                            {
                                app_state.enabled = theme_time.enabled;
                                app_state.theme_index = index;
                                app_state.start = theme_time.start.to_string();
                                app_state.end = theme_time.end.to_string();
                                app_state.apps_light = if theme_time.apps == ThemeColor::Light {
                                    true
                                } else {
                                    false
                                };
                                app_state.system_light = if theme_time.system == ThemeColor::Light {
                                    true
                                } else {
                                    false
                                };
                            }
                            if app_state.theme_index == index {
                                ui.label("Selected");
                            }
                        });
                        ui.separator();
                    }
                });

            ui.horizontal(|ui| {
                if ui.button("Add").clicked() {
                    config.theme_times.push(ThemeTime {
                        enabled: true,
                        start: NaiveTime::from_hms_opt(7, 0, 0).unwrap(),
                        end: NaiveTime::from_hms_opt(20, 0, 0).unwrap(),
                        apps: ThemeColor::Light,
                        system: ThemeColor::Light,
                    });
                }
                if ui.button("Remove").clicked() {
                    if config.theme_times.len() > 1 {
                        config.theme_times.remove(app_state.theme_index);
                        app_state.theme_index -= 1;
                    }
                }
                if ui.button("Up").clicked() && app_state.theme_index > 0 {
                    move_item(
                        &mut config.theme_times,
                        app_state.theme_index,
                        app_state.theme_index - 1,
                    );

                    app_state.theme_index -= 1;
                }
                if ui.button("Down").clicked()
                    && app_state.theme_index + 1 < config.theme_times.len()
                {
                    move_item(
                        &mut config.theme_times,
                        app_state.theme_index,
                        app_state.theme_index + 1,
                    );

                    app_state.theme_index += 1;
                }
            });

            ui.separator();

            ui.label(format!("Selected ThemeTime {}", app_state.theme_index));

            ui.checkbox(&mut app_state.enabled, "ThemeTime Enabled");

            ui.horizontal(|ui| {
                ui.label("Start time : ");
                ui.text_edit_singleline(&mut app_state.start);
            });

            ui.horizontal(|ui| {
                ui.label("End time : ");
                ui.text_edit_singleline(&mut app_state.end);
            });

            let start_time_parsed = NaiveTime::parse_from_str(&app_state.start, "%H:%M:%S");
            let end_time_parsed = NaiveTime::parse_from_str(&app_state.end, "%H:%M:%S");
            let is_incorrect = if start_time_parsed.is_err() || end_time_parsed.is_err() {
                true
            } else {
                false
            };

            ui.horizontal(|ui| {
                ui.checkbox(&mut app_state.apps_light, "Apps light theme.");
                ui.checkbox(&mut app_state.system_light, "System light theme.");
            });

            if is_incorrect {
                Frame::new()
                    .stroke(Stroke::new(1.0, Color32::RED))
                    .show(ui, |ui| {
                        ui.set_width(ui.available_width());
                        ui.label("Inccorect time !");
                    });
            } else {
                ui.label("");

                let c = &mut config.theme_times[app_state.theme_index];

                c.enabled = app_state.enabled;
                c.start = start_time_parsed.unwrap();
                c.end = end_time_parsed.unwrap();
                c.apps = if app_state.apps_light {
                    ThemeColor::Light
                } else {
                    ThemeColor::Dark
                };
                c.system = if app_state.system_light {
                    ThemeColor::Light
                } else {
                    ThemeColor::Dark
                };
            }

            if ui.button("Save config").clicked() {
                match save_config(&config) {
                    Ok(()) => {
                        println!("Saved config successfully.");
                        let _ = fs::write(get_config_folder_path().unwrap().join("needreload"), "");
                    },
                    Err(_) => println!("Error saving config.")
                }
            }
        });
    })
}
