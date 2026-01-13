import time
import threading
from pynput import keyboard

class Recorder:
    def __init__(self):
        self.events = []
        self.start_time = 0
        self.is_recording = False
        self.listener = None
        
    def start_recording(self):
        if self.is_recording:
            return
            
        self.events = []
        self.start_time = time.time()
        self.is_recording = True
        
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()
        
    def stop_recording(self):
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.listener:
            self.listener.stop()
            self.listener = None
            
    def on_press(self, key):
        if not self.is_recording:
            return
        
        try:
            # Calculate delay from start
            timestamp = time.time() - self.start_time
            
            # Identify key
            try:
                key_char = key.char
                key_code = None
            except AttributeError:
                key_char = None
                key_code = str(key) # e.g., Key.space, Key.enter
            
            key_vk = getattr(key, 'vk', None)

            event = {
                'action': 'press',
                'time': timestamp,
                'key_char': key_char,
                'key_code': key_code,
                'vk': key_vk
            }
            self.events.append(event)
        except Exception as e:
            print(f"Error in on_press: {e}")

    def on_release(self, key):
        if not self.is_recording:
            return
            
        try:
            timestamp = time.time() - self.start_time
            
            try:
                key_char = key.char
                key_code = None
            except AttributeError:
                key_char = None
                key_code = str(key)
            
            key_vk = getattr(key, 'vk', None)

            event = {
                'action': 'release',
                'time': timestamp,
                'key_char': key_char,
                'key_code': key_code,
                'vk': key_vk
            }
            self.events.append(event)
        except Exception as e:
            print(f"Error in on_release: {e}")
            
    def get_events(self):
        return self.events
