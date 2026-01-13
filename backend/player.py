import time
import threading
from pynput import keyboard
from pynput.keyboard import Key, Controller

class Player:
    def __init__(self):
        self.controller = Controller()
        self.is_playing = False
        self.stop_flag = False
        self.thread = None

    def start_playback(self, events, speed_factor=1.0, on_finished=None):
        if self.is_playing:
            return

        self.is_playing = True
        self.stop_flag = False
        self.thread = threading.Thread(target=self._play_loop, args=(events, speed_factor, on_finished))
        self.thread.daemon = True
        self.thread.start()

    def stop_playback(self):
        self.stop_flag = True

    def _play_loop(self, events, speed_factor, on_finished):
        if not events:
            self.is_playing = False
            if on_finished:
                on_finished()
            return

        start_time = time.time()
        last_event_time = 0
        
        # Track pressed keys to release them forcefully if stopped
        pressed_keys = set()
        
        try:
            for event in events:
                if self.stop_flag:
                    break
                    
                event_time = event['time']
                
                # Calculate time to wait
                time_diff = event_time - last_event_time
                delay = time_diff / max(0.1, speed_factor)
                
                if delay > 0:
                    time.sleep(delay)
                    
                last_event_time = event_time
                
                # Execute key
                key = self._resolve_key(event)
                if key is not None:
                    if event['action'] == 'press':
                        self.controller.press(key)
                        pressed_keys.add(key)
                    elif event['action'] == 'release':
                        self.controller.release(key)
                        if key in pressed_keys:
                            pressed_keys.remove(key)
                            
        except Exception as e:
            print(f"Error during playback: {e}")
        finally:
            # Cleanup: Release any keys that are still pressed
            for key in pressed_keys:
                try:
                    self.controller.release(key)
                except:
                    pass
            
            self.is_playing = False
            if on_finished:
                on_finished()

    def _execute_key(self, event):
        pass

    def _resolve_key(self, event):
        # 1. Try KeyCode by vk (Virtual Key)
        if event.get('vk'):
            return keyboard.KeyCode.from_vk(event['vk'])

        # 2. Try Special Key Code
        if event['key_code']:
            key_name = event['key_code'].replace('Key.', '')
            if hasattr(Key, key_name):
                return getattr(Key, key_name)
        
        # 3. Try Character
        if event['key_char']:
            return event['key_char']
            
        return None
