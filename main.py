import time
import tkinter as tk
import tkinter.font as tkf
import keyboardlayout as kl
import keyboardlayout.tkinter as klt

from colour import Color
from collections import defaultdict
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
    def __init__(self):
        self._total_count: int = 0
        self._key_count: defaultdict = defaultdict(int)
        
        self._esc_count_to_end: int = 5  # Press 5 times the "esc" key to exit the program.
        self._esc_count: int = 0
        
    def run(self):
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            listener.join()
            
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
                self._compute_stats()
                self._display_stats()
                return False  # Stops listener
        else:
            self._esc_count = 0
            
    def _compute_stats(self):
        self._total_count = sum(list(self._key_count.values()))
        
    def _display_stats(self):
        print(f"TOTAL KEYS PRESSED: {self._total_count}")
        print("--------------")
        print("COUNT PER KEY (DESCENDING ORDER):")
        
        key_count_sorted = sorted(self._key_count.items(), key=lambda item: item[1], reverse=True)
        for key, count in key_count_sorted:
            print(f"{key} -> Pressed {count} times.")
            
    @property
    def key_count(self) -> dict:
        return self._key_count
    

if __name__ == '__main__':
    tracker = KeyboardTracker()
    ts = time.time()
    tracker.run()
    print("=== FINISHED ===")
    tf = time.time() - ts
    print(f"TOTAL TIME: {tf:.2f}")
    keyboard_display = KeyboardDisplay()
    keyboard_display.display(tracker.key_count)