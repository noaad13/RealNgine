# RealNgine

RealNgine is a lightweight Python 3D/2D engine featuring:

* custom 3D models via XML
* software rendering (Pygame or Turtle backend)
* camera system
* input handling (keyboard + mouse)
* real-time world computation pipeline

---

# Installation

RealNgine is **not distributed via pip**.
You must install it manually from GitHub.

## Option 1 — Download ZIP

1. Go to the GitHub repository
2. Click **Code → Download ZIP**
3. Extract the folder
4. Add it to your project or PYTHONPATH

## Option 2 — Git clone

```bash
git clone https://github.com/YOUR_USERNAME/RealNgine.git
```

Then import it directly in your project.

---

# Requirements

RealNgine will install every dependances automatically:
```
pygame
keyboard
lxml
```

---

# Quick Start

```python
from RealNgine.game import World, Player
from RealNgine.render import PygameScene
from RealNgine.models import load_from_xml
from RealNgine.camera import Camera
```

---

# Basic Setup

```python
scene = PygameScene()
camera = Camera()
world = World(scene, camera)
```

---

# Loading a Model

```python
container = load_from_xml("model.xml")
world.containers.append(container)
```

---

# Main Loop

```python
while scene.exists():
    scene.handle_events()
    world.compute()  # Calculate all models
    world.render()  # Render it on screen
```

---

# Player Example

```python
from RealNgine.game import Player

player = Player(
    x=0, y=0, z=0,
    rx=0, ry=0, rz=0,
    cam_x=0, cam_y=120, cam_z=0,  # Eye-level camera
    cam_rx=0, cam_ry=0, cam_rz=0
)
```

### Movement

```python
player.move(1, 0, 0)
player.rotate(0.1, 0, 0)
```

---

# Input System

## Keyboard

```python
from RealNgine.inputs import Listener

listener = Listener()
listener.on_press("space", lambda: print("Jump"))
listener.start()
```

## Mouse (FPS style)

```python
from RealNgine.inputs import MouseMotion

mouse = MouseMotion(scene, sensitivity_x=1.0, sensitivity_y=1.0)
dx, dy = mouse.displacement()
```

## Direct check

```python
from RealNgine.inputs import is_pressed

if is_pressed("w"):
    print("forward")
```

---

# World Utilities

## Find object

```python
obj = world.find("house.door")
```

## Cursor detection

```python
hit = world.what_is_cursor_on()
```

---

# XML Format (Overview)

RealNgine uses a hierarchical XML system:

* `<container>` defines objects
* `<poly>` defines geometry

Containers support:

* position (x, y, z)
* rotation (rx, ry, rz)
* scale (sx, sy, sz)
* inheritance system
* interaction flags

Polygons support:

* vertices list
* color
* local transform

---

# Rendering Backends

## PygameScene (recommended)

* hardware-accelerated buffer system (via DLL)
* Z-buffer rendering
* fullscreen support

## TurtleScene

* debug / educational mode
* slow but simple
* no GPU usage

---

# Notes

* Uses a native DLL (render.dll) for triangle rendering
* All transforms are computed in 3D space
* Camera uses perspective projection
* Engine is still under active development

---

# Status

RealNgine is an experimental engine.
Expect API changes.
