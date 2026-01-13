from pynput import keyboard

class HotkeyManager:
    def __init__(self, callbacks):
        """
        callbacks: dict with keys 'start_record', 'stop_record', 'start_play', 'stop_play'
                   and values being the function to call.
        """
        self.callbacks = callbacks
        # Default hotkeys
        self.hotkeys_map = {
            '<ctrl>+<f8>': self.callbacks['start_record'],
            '<ctrl>+<f9>': self.callbacks['stop_record'],
            '<ctrl>+<f10>': self.callbacks['start_play'],
            '<ctrl>+<f11>': self.callbacks['stop_play']
        }
        self.listener = None

    def start_listening(self):
        if self.listener:
            self.stop_listening()
        
        print("Starting Hotkey Listener...")
        # pynput GlobalHotKeys needs a dict of {key_string: callback}
        try:
            self.listener = keyboard.GlobalHotKeys(self.hotkeys_map)
            self.listener.start()
            print(f"Hotkeys active: {list(self.hotkeys_map.keys())}")
        except Exception as e:
            print(f"Error starting hotkey listener: {e}")

    def stop_listening(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def update_hotkeys(self, new_map):
        rebuilt_map = {}
        for action_name, key_string in new_map.items():
            if action_name in self.callbacks and key_string:
                rebuilt_map[key_string] = self.callbacks[action_name]
        
        self.hotkeys_map = rebuilt_map
        self.start_listening()
