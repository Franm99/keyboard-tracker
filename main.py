import json
import os
import time
import tkinter as tk
import tkinter.font as tkf
import keyboardlayout as kl
import keyboardlayout.tkinter as klt

from colour import Color
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from pynput import keyboard


class KeyboardDisplay:
    def __init__(self):
        self._window = tk.Tk()
        self._window.resizable(False, False)
        
        self._layout_name = kl.LayoutName.QWERTY
        self._key_size = 60
        self._letter_key_size = (self._key_size, self._key_size)  # Key Width and Height
        
        self._color_keyboard = "#414141"
        self._color_key_base = "#bebebe"
        self._color_gr1 = "#32a852"
        self._color_gr2 = "#929693"
        
        self._keyboard_info = kl.KeyboardInfo(
            position=(0, 0),
            padding=2,
            color=self._color_keyboard
        )
        
        self._key_info_dict = {
            "margin": 5,
            "txt_color": "black",
            "txt_font": tkf.Font(family="Arial", size=self._key_size // 4),
            "txt_padding": (self._key_size // 6, self._key_size // 10),
        }
        
        self._key_info_base = kl.KeyInfo(**self._key_info_dict, color=self._color_key_base)
        
        self._keyboard_layout = klt.KeyboardLayout(
            layout_name=self._layout_name,
            keyboard_info=self._keyboard_info,
            letter_key_size=self._letter_key_size,
            key_info=self._key_info_base,
            master=self._window
        )
        
    def display(self, key_press_count: dict):
        self.color_by_count(key_press_count)
        self._window.mainloop()
        
    def color_by_count(self, key_press_count: dict):
        # Sort from highest to lowest press count
        sorted_key_press_count = sorted(key_press_count.items(), key=lambda item: item[1], reverse=True)
        
        highest_count = sorted_key_press_count[0][1]
        lowest_count = sorted_key_press_count[-1][1]
        
        total_diff = highest_count - lowest_count
        values_in_range = list(range(lowest_count, highest_count + 1))
        color_gradient = self._compute_color_gradient(self._color_gr1, self._color_gr2, total_diff + 1)
        
        for key_id, count in sorted_key_press_count:
            idx = values_in_range.index(count)
            color = color_gradient[idx].get_hex()
            
            try:
                kl_key = kl.Key(key_id)
                self._update_key(kl_key, color)
            except ValueError:
                continue
    
    def _update_key(self, key: kl.Key, color: str):
        self._keyboard_layout.update_key(
            key=key,
            key_info=kl.KeyInfo(**self._key_info_dict, color=color)
        )
        
    def _compute_color_gradient(self, color1: str, color2: str, length: int):
        return list(Color(color2).range_to(Color(color1), length))
        

class KeyboardTracker:
    def __init__(self, logger_path: Path = None):
        self._logger_path = logger_path if logger_path else Path("logs")
        
        self._timestamp = datetime.now()
        self._date = self._timestamp.strftime(format="%d-%m-%Y")
        self._hour = self._timestamp.strftime(format="%H:%M:%S")
        
        self.log_data: dict = {
            "date": self._date,
            "duration": "",
            "total_count": 0,
            "keylog": {},
        }
        
        self._total_count: int = 0
        self._key_count: defaultdict = defaultdict(int)
        
        self._esc_count_to_end: int = 5  # Press 5 times the "esc" key to exit the program.
        self._esc_count: int = 0
        
    def run(self):
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            listener.join()
            
    def save(self):
        self.log_data["keylog"] = dict(self._key_count)
        
        end_time = datetime.now()
        duration_s = (end_time - self._timestamp).seconds
        h, m, s = self._seconds_to_hours_string(duration_s)
        
        self.log_data["total_count"] = sum(list(self._key_count.values()))
        self.log_data["duration"] = [h, m, round(s, 4)]
        
        log_file_name = f"record_{self._timestamp.strftime("%m%d%Y_%H%M%S")}.json"
        
        if not os.path.exists(self._logger_path):
            os.makedirs(self._logger_path)
        
        with open(self._logger_path / log_file_name, 'w', encoding="utf-8") as f:
            json.dump(self.log_data, f, indent=4)
            
    def _on_press(self, key, _injected):
        if hasattr(key, "char"):
            key_id = key.char
        elif hasattr(key, "name"):
            key_id = key.name
        else:
            key_id = key
            
        self._key_count[key_id] += 1
        
    def _on_release(self, key, _injected):
        if key == keyboard.Key.esc:
            self._esc_count += 1
            
            if self._esc_count == self._esc_count_to_end:
                print("Stopping keyboard tracker.")
                self._display_stats()
                return False  # Stops listener
        else:
            self._esc_count = 0        
                
    def _display_stats(self):
        print(f"TOTAL KEYS PRESSED: {self._total_count}")
        print("--------------")
        print("COUNT PER KEY (DESCENDING ORDER):")
        
        key_count_sorted = sorted(self._key_count.items(), key=lambda item: item[1], reverse=True)
        for key, count in key_count_sorted:
            print(f"{key} -> Pressed {count} times.")
            
    @staticmethod
    def _seconds_to_hours_string(total_seconds: float) -> tuple:
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        seconds = (total_seconds % 3600) % 60
        
        return hours, mins, seconds

    @property
    def key_count(self) -> dict:
        return self._key_count
    

if __name__ == '__main__':
    tracker = KeyboardTracker()
    ts = time.time()
    tracker.run()
    tracker.save()
    print("=== FINISHED ===")
    tf = time.time() - ts
    print(f"TOTAL TIME: {tf:.2f}")
    keyboard_display = KeyboardDisplay()
    keyboard_display.display(tracker.key_count)