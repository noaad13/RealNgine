from .render import TurtleScene, PygameScene, init as render_init
from importlib.util import find_spec
from . import FROZEN, engine
from .CBindings import ZPixel, INVALID_TRIANGLE
from .camera import Camera
from pathlib import Path
import subprocess
import ctypes
import math
import json
import time
import sys

if FROZEN:
    CD = Path(sys.executable).parent
else:
    CD = Path(__file__).parent.parent
BUFFERS_DLL = str(CD / "Clibs" / "buffers.dll")

# -- Liaison avec la DLL --
buffers = ctypes.CDLL(BUFFERS_DLL)

buffers.draw_triangle.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),  # color buffer
    ctypes.POINTER(ZPixel),  # z-buffer
    ctypes.c_int,  # screen width
    ctypes.c_int,  # screen height
    ctypes.c_float, ctypes.c_float, ctypes.c_float,  # V1
    ctypes.c_float, ctypes.c_float, ctypes.c_float,  # V2
    ctypes.c_float, ctypes.c_float, ctypes.c_float,  # v3
    ctypes.c_uint8,  # R
    ctypes.c_uint8,  # G
    ctypes.c_uint8,  # B
    ctypes.c_uint16   # triangle id
]

buffers.cursor_hit.argtypes = [
    ctypes.POINTER(ZPixel),  # z-buffer
    ctypes.c_int,  # screen width
    ctypes.c_int,
]
buffers.cursor_hit.restype = ctypes.c_uint16

buffers.clear_buffers.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.POINTER(ZPixel),
    ctypes.c_int,
    ctypes.c_int,
]

buffers.cursor_hit.argstypes = [
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.POINTER(ZPixel)
]

def init(gpu=False):
    render_init(gpu)
    engine.init(gpu)

def point_in_polygon(polygon, point=(0, 0)):  # Algorithme pour déterminer si on est à l'intérieur du polygon
    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xinters = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xinters:
                inside = not inside
    return inside

class World:
    def __init__(self, scene, camera, auto_update=True, resolution=10):
        self.scene = scene
        self.camera = camera
        self.containers = []
        self.computed = []
        self.auto_update = auto_update

    def done(self):  # Important pour savoir quels sont les parents de tout objet
        def set_h(obj, parent):
            obj.parent = parent
            if isinstance(obj, engine.Container3d):
                for child in obj.children:
                    set_h(child, obj)
        for container in self.containers:
            set_h(container, None)

    def find(self, name):  # Renvoie un objet Polygon3d ou Container3d à partir de son chemin. Ex: house.wall1.door -> <Container3d at 0x....>
        def walk(c):
            if c.path == name:
                return c
            for child in c.children:
                if isinstance(child, engine.Container3d):
                    found_ = walk(child)
                    if found_:
                        return found_
            return None
        for container in self.containers:
            found = walk(container)
            if found:
                return found
        return None

    def compute(self):  # Compute tous les objets du monde
        self.computed = []
        for obj3d in self.containers:
            obj3d.compute(self.camera)
            self.computed.extend(obj3d.computed)
        if isinstance(self.scene, TurtleScene):  # Seulement pour Average Z
            self.computed = sorted(self.computed, key=lambda polygon: polygon.average_z, reverse=True)

    def render(self):
        if isinstance(self.scene, TurtleScene):
            self.scene.clear()
            for polygon3d in self.computed:
                polygon2d = [coords[:2] for coords in polygon3d.computed]
                self.scene.fill_polygon(polygon2d, polygon3d.color, polygon3d.borderwidth)
        elif isinstance(self.scene, PygameScene):
            buffer_ptr = ctypes.cast(self.scene.buffer, ctypes.POINTER(ctypes.c_uint8))  # Permet d'envoyer le pointeur à la dll
            zbuffer_ptr = ctypes.cast(self.scene.zbuffer, ctypes.POINTER(ZPixel))  # Pareil
            buffers.clear_buffers(buffer_ptr, zbuffer_ptr, self.scene.width, self.scene.height)  # Fonction de la DLL pour effacer rapidement les buffers
            for polygon3d in self.computed:
                v = polygon3d.computed
                if len(v) < 3:
                    continue
                v1 = v[0]
                for i in range(1, len(v) - 1):
                    v2 = v[i]
                    v3 = v[i + 1]
                    r, g, b = polygon3d.color
                    buffers.draw_triangle(
                        buffer_ptr,
                        zbuffer_ptr,
                        self.scene.width,
                        self.scene.height,
                        ctypes.c_float(v1[0]),
                        ctypes.c_float(v1[1]),
                        ctypes.c_float(v1[2]),
                        ctypes.c_float(v2[0]),
                        ctypes.c_float(v2[1]),
                        ctypes.c_float(v2[2]),
                        ctypes.c_float(v3[0]),
                        ctypes.c_float(v3[1]),
                        ctypes.c_float(v3[2]),
                        ctypes.c_uint8(r),
                        ctypes.c_uint8(g),
                        ctypes.c_uint8(b),
                        ctypes.c_uint16(polygon3d.triangle_id)
                    )
        if self.auto_update:
            self.scene.update()

    def what_is_cursor_on(self):  # Quel polygone le curseur touche
        triangle_id = buffers.cursor_hit(self.scene.zbuffer, self.scene.width, self.scene.height)
        if triangle_id == INVALID_TRIANGLE:
            return None
        if triangle_id >= len(engine.triangles):
            return None
        return engine.triangles[triangle_id]

    def parent(self, obj3d):  # Renvoie le parent de l'objet
        if not obj3d.parents:
            return None
        try:
            path = ".".join(obj3d.parents)
        except Exception as e:
            raise e
        return self.find(path)

    @staticmethod
    def is_parent(container, parent_path):  # Renvoie si le chemin du parent donné est un parent de l'objet
        parent = ".".join(container.parents)
        if parent_path in parent and parent.startswith(parent_path):
            return True
        return False

    def is_cursor_touching(self, parent_path):
        touched = self.what_is_cursor_on()
        return self.is_parent(touched, parent_path)

class Player:  # Objet joueur (aura un model dans le futur)
    def __init__(self, x, y, z, rx, ry, rz, cam_x, cam_y, cam_z, cam_rx, cam_ry, cam_rz):
        self.camera = Camera()
        self.x, self.y, self.z = x, y, z
        self.rx, self.ry, self.rz = rx, ry, rz
        self.cam_x, self.cam_y, self.cam_z = cam_x, cam_y, cam_z
        self.cam_rx, self.cam_ry, self.cam_rz = cam_rx, cam_ry, cam_rz
        self.camera.x = self.x + self.cam_x
        self.camera.y = self.y + self.cam_y
        self.camera.z = self.z + self.cam_z
        self.camera.rx = (self.rx + self.cam_rx) % (2 * math.pi)
        self.camera.ry = (self.ry + self.cam_ry) % (2 * math.pi)
        self.camera.rz = (self.rz + self.cam_rz) % (2 * math.pi)
        self.crouched = False
        self.inventory = []

    def goto(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.camera.x = x + self.cam_x
        self.camera.y = y + self.cam_y
        self.camera.z = z + self.cam_z

    def move(self, x, y, z):
        self.x += x
        self.y += y
        self.z += z
        self.goto(self.x, self.y, self.z)

    def rotate_to(self, rx, ry, rz):
        self.rx = rx
        self.ry = ry
        self.rz = rz
        self.camera.rx = (rx + self.cam_rx + math.pi) % (2 * math.pi) - math.pi  # rx € [-π;π]
        self.camera.ry = (ry + self.cam_ry + math.pi) % (2 * math.pi) - math.pi  # ry € [-π;π]
        self.camera.rz = (rz + self.cam_rz + math.pi) % (2 * math.pi) - math.pi  # rz € [-π;π]

    def rotate(self, rx, ry, rz):
        self.rx += rx
        if abs(self.rx) > math.pi / 2:  # Clamp pitch
            if not abs(rx):
                rel = 1
            else:
                rel = rx / abs(rx)
            self.rx = math.pi / 2 * rel
        self.ry += ry
        self.rz += rz
        self.rotate_to(self.rx, self.ry, self.rz)

    def new_item(self, item_id):
        self.inventory.append(item_id)

    def has_item(self, item_id):
        return item_id in self.inventory

    def del_item(self, item_id):
        if self.has_item(item_id):
            self.inventory.remove(item_id)

class Clocks:  # Appelle des fonctions toutes les x secondes
    def __init__(self):
        self.clocks = {}

    def add(self, name, s, func):
        self.clocks[name] = [time.perf_counter(), s, func]

    def check(self):
        reset = []
        for name, clock in self.clocks.items():
            if time.perf_counter() >= clock[0] + clock[1]:
                clock[2]()
                reset.append(name)
        for n in reset:
            self.clocks[n][0] = time.perf_counter()
