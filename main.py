import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import sys
import json

# Add current directory to path so we can import backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.recorder import Recorder
from backend.player import Player
from backend.file_handler import FileHandler
from backend.hotkey_manager import HotkeyManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_user_data_dir():
    """Get the user-writable data directory for this application."""
    # Use Local AppData (e.g., C:\Users\Username\AppData\Local)
    base_path = os.getenv('LOCALAPPDATA')
    if not base_path:
        base_path = os.path.expanduser('~')
        
    data_dir = os.path.join(base_path, "AutoKeyboardRepeaterPro")
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
        except Exception as e:
            print(f"Error creating data directory: {e}")
            
    return data_dir

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Auto Keyboard Repeater Pro")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Set Icon
        try:
            icon_path = get_resource_path("app_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error loading icon: {e}")
            
        # Setup paths (User Data Directory)
        self.data_dir = get_user_data_dir()
        self.recordings_dir = os.path.join(self.data_dir, "recordings")
        self.settings_file = os.path.join(self.data_dir, "settings.json")

        # Create recordings dir if it doesn't exist
        if not os.path.exists(self.recordings_dir):
            try:
                os.makedirs(self.recordings_dir)
            except Exception as e:
                print(f"Error creating recordings directory: {e}")
                
        print(f"Data Directory: {self.data_dir}") # Debug log

        # Default Settings
        self.settings = {
            "speed": 1.0,
            "hotkeys": {
                'start_record': '<ctrl>+<f8>',
                'stop_record': '<ctrl>+<f9>',
                'start_play': '<ctrl>+<f10>',
                'stop_play': '<ctrl>+<f11>'
            }
        }
        self.load_settings()

        # Backend Components
        self.recorder = Recorder()
        self.player = Player()
        self.current_events = []
        self.filename = None

        # State
        self.app_state = "IDLE" 

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Status
        self.grid_rowconfigure(1, weight=1) # Controls
        self.grid_rowconfigure(2, weight=0) # Settings

        # --- Status Bar ---
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Ready", font=("Roboto", 16, "bold"))
        self.status_label.pack(pady=10)
        self.event_count_label = ctk.CTkLabel(self.status_frame, text="Events: 0")
        self.event_count_label.pack(pady=5)

        # --- Main Controls ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.control_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_record = ctk.CTkButton(self.control_frame, text=f"Record ({self.settings['hotkeys']['start_record']})", command=self.start_recording, fg_color="#e74c3c", hover_color="#c0392b")
        self.btn_record.grid(row=0, column=0, padx=5, pady=20)

        self.btn_stop = ctk.CTkButton(self.control_frame, text=f"Stop ({self.settings['hotkeys']['stop_record']})", command=self.stop_action, fg_color="#7f8c8d", hover_color="#95a5a6")
        self.btn_stop.grid(row=0, column=1, padx=5, pady=20)

        self.btn_play = ctk.CTkButton(self.control_frame, text=f"Play ({self.settings['hotkeys']['start_play']})", command=self.start_playback, fg_color="#2ecc71", hover_color="#27ae60")
        self.btn_play.grid(row=0, column=2, padx=5, pady=20)

        # File Selection Dropdown
        self.file_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.file_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
        
        self.lbl_select = ctk.CTkLabel(self.file_frame, text="Select Recording:")
        self.lbl_select.pack(side="left", padx=5)
        
        self.file_option_menu = ctk.CTkOptionMenu(self.file_frame, values=[], command=self.on_file_selected)
        self.file_option_menu.pack(side="left", fill="x", expand=True, padx=5)
        self.file_option_menu.set("Select a file...")

        self.btn_refresh = ctk.CTkButton(self.file_frame, text="↻", width=30, command=self.refresh_file_list)
        self.btn_refresh.pack(side="left", padx=5)

        # File Controls
        self.btn_save = ctk.CTkButton(self.control_frame, text="Save As New", command=self.save_file)
        self.btn_save.grid(row=2, column=0, padx=5, pady=10)

        # --- Settings / Speed ---
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.speed_label = ctk.CTkLabel(self.settings_frame, text=f"Playback Speed: {int(self.settings['speed']*100)}%")
        self.speed_label.pack(pady=5)
        
        self.speed_slider = ctk.CTkSlider(self.settings_frame, from_=0.1, to=100.0, number_of_steps=999, command=self.update_speed_label)
        self.speed_slider.set(self.settings['speed'])
        self.speed_slider.pack(pady=5, padx=20, fill="x")

        self.btn_hotkeys = ctk.CTkButton(self.settings_frame, text="Configure Hotkeys", command=self.open_hotkey_config, fg_color="transparent", border_width=1)
        self.btn_hotkeys.pack(pady=10)

        # Hotkey Manager
        self.hotkey_manager = HotkeyManager({
            'start_record': lambda: self.after(0, self.start_recording),
            'stop_record': lambda: self.after(0, self.stop_action),
            'start_play': lambda: self.after(0, self.start_playback),
            'stop_play': lambda: self.after(0, self.stop_action)
        })
        # Apply loaded settings to manager
        self.hotkey_manager.update_hotkeys(self.settings['hotkeys'])

        # Initial scan
        self.refresh_file_list()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    # Merge keys safely
                    if "speed" in data:
                        self.settings["speed"] = float(data["speed"])
                    if "hotkeys" in data:
                        self.settings["hotkeys"].update(data["hotkeys"])
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_speed_label(self, value):
        percentage = int(value * 100)
        self.speed_label.configure(text=f"Playback Speed: {percentage}%")
        self.settings['speed'] = value
        
    def refresh_file_list(self):
        if not os.path.exists(self.recordings_dir):
             self.file_option_menu.configure(values=["No .rsmk files found"])
             return

        files = [f for f in os.listdir(self.recordings_dir) if f.endswith('.rsmk')]
        
        if files:
            self.file_option_menu.configure(values=files)
            if self.filename and self.filename in files:
                self.file_option_menu.set(self.filename)
            else:
                self.file_option_menu.set(files[0])
                self.on_file_selected(files[0])
        else:
            self.file_option_menu.configure(values=["No .rsmk files found"])
            self.file_option_menu.set("No .rsmk files found")

    def on_file_selected(self, filename):
        if not filename or filename == "No .rsmk files found":
            return
            
        self.filename = filename
        try:
            full_path = os.path.join(self.recordings_dir, filename)
            self.current_events = FileHandler.load_recording(full_path)
            self.event_count_label.configure(text=f"Events: {len(self.current_events)}")
            self.status_label.configure(text=f"Loaded: {filename}", text_color="white")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")

    def start_recording(self):
        if self.app_state != "IDLE":
            return
        
        self.app_state = "RECORDING"
        self.status_label.configure(text="Status: Recording...", text_color="#e74c3c")
        self.recorder.start_recording()
        
        self.btn_play.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        self.file_option_menu.configure(state="disabled")

    def stop_action(self):
        if self.app_state == "RECORDING":
            self.recorder.stop_recording()
            self.current_events = self.recorder.get_events()
            self.app_state = "IDLE"
            self.status_label.configure(text="Status: Recorded (Unsaved)", text_color="white")
            self.event_count_label.configure(text=f"Events: {len(self.current_events)}")
            self.btn_play.configure(state="normal")
            self.btn_save.configure(state="normal")
            self.file_option_menu.configure(state="normal")
            
        elif self.app_state == "PLAYING":
            self.player.stop_playback()
            self.app_state = "IDLE"
            self.status_label.configure(text="Status: Stopped", text_color="white")
            self.btn_record.configure(state="normal")
            self.file_option_menu.configure(state="normal")

    def start_playback(self):
        if self.app_state != "IDLE" or not self.current_events:
            if not self.current_events:
                messagebox.showwarning("Warning", "No recording loaded/recorded.")
            return
            
        speed = self.speed_slider.get()
        self.app_state = "PLAYING"
        self.status_label.configure(text=f"Status: Playing ({int(speed*100)}%)", text_color="#2ecc71")
        self.btn_record.configure(state="disabled")
        self.file_option_menu.configure(state="disabled")
        
        self.player.start_playback(self.current_events, speed_factor=speed, on_finished=self.on_playback_finished)

    def on_playback_finished(self):
        self.after(0, self._on_playback_finished_main)
        
    def _on_playback_finished_main(self):
        self.app_state = "IDLE"
        self.status_label.configure(text="Status: Playback Finished", text_color="white")
        self.btn_record.configure(state="normal")
        self.file_option_menu.configure(state="normal")

    def save_file(self):
        if not self.current_events:
            return
        
        initial_dir = self.recordings_dir
        
        filepath = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".rsmk", 
            filetypes=[("RSMK Files", "*.rsmk")]
        )
        if filepath:
            try:
                FileHandler.save_recording(filepath, self.current_events)
                messagebox.showinfo("Success", "Recording saved successfully.")
                self.refresh_file_list() 
                filename = os.path.basename(filepath)
                if os.path.dirname(os.path.abspath(filepath)) == os.path.abspath(self.recordings_dir):
                    self.on_file_selected(filename)
                    self.file_option_menu.set(filename)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

    def open_hotkey_config(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Configure Hotkeys")
        dialog.geometry("400x300")
        dialog.attributes("-topmost", True)

        def create_row(row, label_text, key):
            lbl = ctk.CTkLabel(dialog, text=label_text)
            lbl.grid(row=row, column=0, padx=10, pady=10)
            entry = ctk.CTkEntry(dialog)
            entry.insert(0, self.settings['hotkeys'][key])
            entry.grid(row=row, column=1, padx=10, pady=10)
            return entry

        e_rec = create_row(0, "Start Recording:", "start_record")
        e_stop_rec = create_row(1, "Stop Recording:", "stop_record")
        e_play = create_row(2, "Start Playback:", "start_play")
        e_stop_play = create_row(3, "Stop Playback:", "stop_play")

        def save_keys():
            new_map = {
                'start_record': e_rec.get(),
                'stop_record': e_stop_rec.get(),
                'start_play': e_play.get(),
                'stop_play': e_stop_play.get()
            }
            # Update settings and save immediately
            self.settings['hotkeys'] = new_map
            self.save_settings()
            
            # Update Manager and UI
            self.hotkey_manager.update_hotkeys(new_map)
            
            self.btn_record.configure(text=f"Record ({new_map['start_record']})")
            self.btn_stop.configure(text=f"Stop ({new_map['stop_record']})") # This button covers two actions, simplifying text
            self.btn_play.configure(text=f"Play ({new_map['start_play']})")
            
            dialog.destroy()

        btn_apply = ctk.CTkButton(dialog, text="Apply & Save", command=save_keys)
        btn_apply.grid(row=4, column=0, columnspan=2, pady=20)

    def on_closing(self):
        # Save speed on exit
        self.settings['speed'] = self.speed_slider.get()
        self.save_settings()
        
        self.hotkey_manager.stop_listening()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
