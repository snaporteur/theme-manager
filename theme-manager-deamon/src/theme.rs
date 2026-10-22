use theme_manager_common::ThemeColor;
use windows_sys::Win32::UI::WindowsAndMessaging::{HWND_BROADCAST, SMTO_ABORTIFHUNG, SendMessageTimeoutW, WM_SETTINGCHANGE};
use winreg::{
    RegKey,
    enums::{HKEY_CURRENT_USER, KEY_SET_VALUE},
};

const PERSONALIZE: &str = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize";

pub struct Theme {
    apps: ThemeColor,
    system: ThemeColor,
}

impl Theme {
    pub fn new() -> Self {
        Theme { apps: ThemeColor::Light, system: ThemeColor::Light }
    }

    pub fn set_apps_color(&mut self, state: ThemeColor) {
        self.apps = state;
    }

    pub fn set_system_color(&mut self, state: ThemeColor) {
        self.system = state;
    }

    fn set_windows_theme(&self) {
        let hkcu = RegKey::predef(HKEY_CURRENT_USER);
        let key = hkcu
            .open_subkey_with_flags(PERSONALIZE, KEY_SET_VALUE)
            .expect("Failed to access to the personnalize key.");

        if self.apps == ThemeColor::Light {
            key.set_value("AppsUseLightTheme", &1u32)
                .expect("Failed to set the apps theme");
        } else {
            key.set_value("AppsUseLightTheme", &0u32)
                .expect("Failed to set the apps theme");
        }

        if self.system == ThemeColor::Light {
            key.set_value("SystemUsesLightTheme", &1u32)
                .expect("Failed to set the system theme");
        } else {
            key.set_value("SystemUsesLightTheme", &0u32)
                .expect("Failed to set the system theme");
        }
    }

    fn send_windows_broadcast(&self) {
        let param: Vec<u16> = "ImmersiveColorSet\0".encode_utf16().collect();
        let mut result: usize = 0;
        unsafe {
            SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                param.as_ptr() as isize,
                SMTO_ABORTIFHUNG,
                100,
                &mut result,
            );
        }
    }

    pub fn apply(&self) {
        self.set_windows_theme();
        self.send_windows_broadcast();
    }
}
