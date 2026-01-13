import json
import os

class FileHandler:
    @staticmethod
    def save_recording(filepath, events):
        """Saves events to an .rsmk file (JSON format)."""
        data = {
            "version": "1.0",
            "events": events
        }
        
        # Ensure correct extension
        if not filepath.endswith('.rsmk'):
            filepath += '.rsmk'
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=None)
            
    @staticmethod
    def load_recording(filepath):
        """Loads events from an .rsmk file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError("File not found.")
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        return data.get("events", [])
