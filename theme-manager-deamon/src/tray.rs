use std::{process::Command, sync::mpsc::Receiver};

use trayicon::{MenuBuilder, TrayIcon, TrayIconBuilder};

use windows_sys::Win32::UI::WindowsAndMessaging::*;

/// Mode de fonctionnement choisi depuis le menu du tray.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ThemeMode {
    /// Suit les plages horaires de la config.
    Auto,
    /// Force le thème clair, quelle que soit la plage active.
    ForceLight,
    /// Force le thème sombre, quelle que soit la plage active.
    ForceDark,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Events {
    Open,
    Mode(ThemeMode),
    Quit,
}

const MODES: [ThemeMode; 3] = [ThemeMode::Auto, ThemeMode::ForceLight, ThemeMode::ForceDark];

pub struct Tray {
    object: TrayIcon<Events>,
    receiver: Receiver<Events>,
    mode: ThemeMode,
}

impl Tray {
    pub fn new() -> Self {
        let (s, r) = std::sync::mpsc::channel::<Events>();
        let mode = ThemeMode::Auto;

        let o = TrayIconBuilder::new()
            .sender(move |e: &Events| {
                let _ = s.send(*e);
            })
            .icon_from_buffer(include_bytes!("icon.ico"))
            .tooltip(&Self::tooltip(mode))
            .on_click(Events::Open)
            .menu(
                MenuBuilder::new()
                    .item("Open", Events::Open)
                    .separator()
                    .checkable("Automatique (plages horaires)", true, Events::Mode(ThemeMode::Auto))
                    .checkable("Forcer le thème clair", false, Events::Mode(ThemeMode::ForceLight))
                    .checkable("Forcer le thème sombre", false, Events::Mode(ThemeMode::ForceDark))
                    .separator()
                    .item("Close", Events::Quit),
            )
            .build()
            .unwrap();

        Tray {
            object: o,
            receiver: r,
            mode,
        }
    }

    fn tooltip(mode: ThemeMode) -> String {
        let label = match mode {
            ThemeMode::Auto => "automatique",
            ThemeMode::ForceLight => "clair forcé",
            ThemeMode::ForceDark => "sombre forcé",
        };
        format!("ThemeManager V2 ({label})")
    }

    /// Mode actuellement sélectionné dans le tray.
    pub fn mode(&self) -> ThemeMode {
        self.mode
    }

    fn set_mode(&mut self, mode: ThemeMode) {
        self.mode = mode;
        for m in MODES {
            let _ = self.object.set_menu_item_checkable(Events::Mode(m), m == mode);
        }
        let _ = self.object.set_tooltip(&Self::tooltip(mode));
    }

    pub fn process_until_close(&mut self) -> bool {
        unsafe {
            let mut msg: MSG = std::mem::zeroed();
            while PeekMessageW(&mut msg, std::ptr::null_mut(), 0, 0, PM_REMOVE) != 0 {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
        }

        while let Ok(evt) = self.receiver.try_recv() {
            match evt {
                Events::Open => { let _ = Command::new("theme-manager-panel.exe").spawn(); }
                Events::Mode(mode) => self.set_mode(mode),
                Events::Quit => return false,
            }
        }

        true
    }
}
