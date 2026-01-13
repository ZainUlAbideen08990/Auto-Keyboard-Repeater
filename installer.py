import customtkinter as ctk
import os
import sys
import shutil
import threading
import subprocess
from tkinter import messagebox

# Configuration
APP_NAME = "Auto Keyboard Repeater Pro"
EXE_NAME = "AutoKeyboardRepeaterPro.exe"
# Start with a default, but allow user to change
DEFAULT_INSTALL_DIR = os.path.join(os.environ['LOCALAPPDATA'], "Programs", APP_NAME)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_bundle_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Install {APP_NAME}")
        self.geometry("500x350")
        self.resizable(False, False)

        # Set Icon
        try:
            icon_path = os.path.join(get_bundle_dir(), "app_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error loading icon: {e}")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # Title
        self.lbl_title = ctk.CTkLabel(self, text=f"Welcome to the {APP_NAME} Installer", font=("Roboto", 20, "bold"))
        self.lbl_title.grid(row=0, column=0, pady=20)

        # Path Selection
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_path = ctk.CTkLabel(self.path_frame, text="Install Location:")
        self.lbl_path.pack(side="top", anchor="w", padx=10, pady=5)
        
        self.entry_path = ctk.CTkEntry(self.path_frame)
        self.entry_path.insert(0, DEFAULT_INSTALL_DIR)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        self.btn_browse = ctk.CTkButton(self.path_frame, text="Browse", width=60, command=self.browse_folder)
        self.btn_browse.pack(side="right", padx=10, pady=10)

        # Options
        self.chk_shortcut = ctk.CTkCheckBox(self, text="Create Desktop Shortcut", onvalue=True, offvalue=False)
        self.chk_shortcut.select()
        self.chk_shortcut.grid(row=2, column=0, pady=10)

        # Install Button
        self.btn_install = ctk.CTkButton(self, text="Install", command=self.start_install, font=("Roboto", 16, "bold"), height=40)
        self.btn_install.grid(row=3, column=0, pady=20)

        # Status
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.lbl_status = ctk.CTkLabel(self, text="")

    def browse_folder(self):
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, os.path.join(folder, APP_NAME))

    def start_install(self):
        self.btn_install.configure(state="disabled")
        self.entry_path.configure(state="disabled")
        self.btn_browse.configure(state="disabled")
        
        self.progress.grid(row=4, column=0, padx=20, pady=(0,10), sticky="ew")
        self.lbl_status.grid(row=5, column=0, pady=(0,20))
        
        thread = threading.Thread(target=self.run_installation)
        thread.start()

    def run_installation(self):
        install_dir = self.entry_path.get()
        create_shortcut = self.chk_shortcut.get()
        
        try:
            # 1. Create Directory
            self.update_status("Creating directories...", 0.2)
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)
            
            # 2. Copy Executable
            self.update_status("Copying application files...", 0.4)
            src_exe = os.path.join(get_bundle_dir(), EXE_NAME)
            dst_exe = os.path.join(install_dir, EXE_NAME)
            
            if not os.path.exists(src_exe):
                 raise FileNotFoundError(f"Installer corrupted: {EXE_NAME} not found inside bundle.")
                 
            shutil.copy2(src_exe, dst_exe)
            
            # 4. Create Shortcut
            if create_shortcut:
                self.update_status("Creating shortcut...", 0.8)
                try:
                    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
                    shortcut_path = os.path.join(desktop, f"{APP_NAME}.lnk")
                    
                    # PowerShell command to create a shortcut with icon
                    # We point the icon to the installed exe which now contains the icon
                    ps_script = f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut_path}'); $s.TargetPath = '{dst_exe}'; $s.WorkingDirectory = '{install_dir}'; $s.IconLocation = '{dst_exe}'; $s.Save()"
                    subprocess.run(["powershell", "-Command", ps_script], check=True, capture_output=True)
                except Exception as e:
                    print(f"Shortcut creation error: {e}")

            self.update_status("Installation Complete!", 1.0)
            self.btn_install.configure(text="Exit", command=self.destroy, state="normal", fg_color="green")
            
        except PermissionError:
            self.update_status("Error: Access Denied.", 0.0)
            self.lbl_status.configure(text_color="red")
            messagebox.showerror("Permission Error", "Access Denied!\n\nTo install to this folder (e.g., Program Files), you must Run as Administrator.\n\nRight-click the installer and select 'Run as Administrator', or choose a different folder (like your User folder).")
            self.btn_install.configure(state="normal")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", 0.0)
            self.lbl_status.configure(text_color="red")
            self.btn_install.configure(state="normal")

    def update_status(self, text, progress):
        self.lbl_status.configure(text=text)
        self.progress.set(progress)

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
