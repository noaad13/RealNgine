import threading
import keyboard
import ctypes
import time

class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]

class cursor:
    __pt = Point()

    @staticmethod
    def position():
        ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor.__pt))
        return cursor.__pt.x, cursor.__pt.y

class Listener:
    def __init__(self):
        self.pressed = []
        self._on_pressed = {}
        self._on_release = {}
        self._on_down = {}
        self._keys = []
        self._stop = threading.Event()

    def __listen(self):
        while not self._stop.is_set():
            for k in self._keys:
                if keyboard.is_pressed(k):
                    if k in self._on_down.keys():
                        self._on_down[k]()
                    if k not in self.pressed:
                        self.pressed.append(k)
                        if k in self._on_pressed.keys():
                            self._on_pressed[k]()
                elif k in self.pressed:
                    self.pressed.remove(k)
                    if k in self._on_release.keys():
                        self._on_release[k]()
            time.sleep(0.01)

    def start(self):
        self._stop = threading.Event()
        threading.Thread(target=self.__listen, daemon=True).start()
        # self.__listen()

    def stop(self):
        self._stop.set()

    def on_press(self, hotkey, func):
        self._on_pressed[hotkey] = func
        if hotkey not in self._keys:
            self._keys.append(hotkey)

    def on_release(self, hotkey, func):
        self._on_release[hotkey] = func
        if hotkey not in self._keys:
            self._keys.append(hotkey)

    def on_key_down(self, hotkey, func):
        self._on_down[hotkey] = func
        if hotkey not in self._keys:
            self._keys.append(hotkey)

class MouseMotion:
    def __init__(self, scene, sensitivity_x=1, sensitivity_y=1):
        self.t = None
        self.scene = scene
        self.sensitivity = (sensitivity_x, sensitivity_y)
        user32 = ctypes.windll.user32
        self.mid_x, self.mid_y = user32.GetSystemMetrics(0) // 2, user32.GetSystemMetrics(1) // 2
        self.scene.hide_mouse()

    def displacement(self):
        if self.t is None:
            dt = 0
        else:
            dt = time.perf_counter() - self.t
        x, y = cursor.position()
        dx, dy = x - self.mid_x, y - self.mid_y
        self.t = time.perf_counter()
        ctypes.windll.user32.SetCursorPos(self.mid_x, self.mid_y)
        return dx * dt * self.sensitivity[0], dy * dt * self.sensitivity[1]

def is_pressed(hotkey):
    return keyboard.is_pressed(hotkey)
