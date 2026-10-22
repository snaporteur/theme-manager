use std::{process::Command, sync::mpsc::Receiver};

use trayicon::{MenuBuilder, TrayIcon, TrayIconBuilder};

use windows_sys::Win32::UI::WindowsAndMessaging::*;

#[derive(Clone, Copy, PartialEq, Eq)]
enum Events {
    Open,
    Quit,
}

pub struct Tray {
    _object: TrayIcon<Events>,
    receiver: Receiver<Events>
}

impl Tray {
    pub fn new() -> Self {
        let (s, r) = std::sync::mpsc::channel::<Events>();

        let o = TrayIconBuilder::new()
            .sender(move |e: &Events| {
                let _ = s.send(*e);
            })
            .icon_from_buffer(include_bytes!("icon.ico"))
            .tooltip("ThemeManager V2")
            .on_click(Events::Open)
            .menu(
                MenuBuilder::new()
                    .item("Open", Events::Open)
                    .item("Close", Events::Quit),
            )
            .build()
            .unwrap();

        Tray {
            _object: o,
            receiver: r
        }
    }

    pub fn process_until_close(&self) -> bool {
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
                Events::Quit => return false,
            }
        }

        true
    }
}
