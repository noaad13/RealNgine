from RealNgine import inputs, models, init
import turtle
import math
import time

def interaction():  # Quand "E" est pressé
    global door
    global key
    global player
    hit = world.what_is_cursor_on()
    if not hit:
        return
    if world.is_parent(hit, "door") and door.average_z < INTERACT_RANGE:
        if door.value("locked"):
            if player.has_item("key"):
                door.value("locked", False)
                player.del_item("key")
        if not door.value("locked"):
            if door.value("open"):
                door.value("open", False)
                door.ry = math.pi
            else:
                door.value("open", True)
                door.ry = math.pi / 2 * 3
    if world.is_parent(hit, "key"):
        key.hidden = True
        player.new_item("key")

def crouch():  # Quand shift est pressé
    global player
    if player.crouched:
        player.cam_y = CAMERA_PLAYER_OFF_Y
    else:
        player.cam_y = CAMERA_PLAYER_OFF_Y - 30
    player.move(0, 0, 0)
    player.crouched = not player.crouched

def can_interact():  # Te dis si l'objet que tu regardes à un parent intéractif
    global on_interactive
    hit = world.what_is_cursor_on()
    if not hit:
        on_interactive = False
        return
    container = world.parent(hit)
    on_interactive = container.interactive and container.average_z < INTERACT_RANGE

def FPS():
    global fps
    global fps_count
    fps = fps_count
    fps_count = 0

GPU = True  # False = Turtle + Average Z   |   True = Pygame + Z-buffer
MAX_FPS = 120  # Juste pour éviter dt=0
MIN_DT = 1 / MAX_FPS
RES = 20  # Pas utilisé pour l'instant

# Touches
FORWARD = "z"
BACKWARD = "s"
LEFT = "q"
RIGHT = "d"
CAM_LEFT = "left"
CAM_RIGHT = "right"
CAM_UP = "up"
CAM_DOWN = "down"
CROUCH = "shift"
INTERACT = "e"

# Constantes modifiables
CAMERA_FOCAL_LENGHT = 400
INTERACT_RANGE = 200
PLAYER_SPEED = 200
CAMERA_KEYBOARD_LOOK_SPEED = 2
CAMERA_MOUSE_LOOK_SPEED_X = 0.01
CAMERA_MOUSE_LOOK_SPEED_Y = 0.01
CAMERA_PLAYER_OFF_X = 0
CAMERA_PLAYER_OFF_Y = 140
CAMERA_PLAYER_OFF_Z = 0

# Curseur
CURSOR_MIN_RADIUS = 2
CURSOR_MAX_RADIUS = 4

init(GPU)

player = RealNgine.game.Player(0, 0, 0, 0, 0, 0, CAMERA_PLAYER_OFF_X, CAMERA_PLAYER_OFF_Y, CAMERA_PLAYER_OFF_Z, 0, 0, 0)  # Le joueur a une caméra par défaut
player.camera.focal_lenght = CAMERA_FOCAL_LENGHT

# --- Containers import ---
table = models.load_from_xml("models/table.xml", debug=True)
key = models.load_from_xml("models/key.xml", debug=True)
house = models.load_from_xml("models/house.xml", debug=True)
door = models.load_from_xml("models/door.xml", debug=True)

# --- Configuration des containers ---
table.children.append(key)  # Key fait partie de la table
house.children.append(door)
door.z = 500
key.rx = math.pi / 2
key.y = 5

if GPU:
    scene = RealNgine.render.PygameScene()
else:
    scene = RealNgine.render.TurtleScene()

# Ton container monde unique
world = RealNgine.game.World(scene, player.camera, auto_update=False, resolution=RES)

# Ajout des containers au monde (pas besoin d'inclure key puisqu'il fait partie de table)
world.containers += [table, house]

# Finalisation du world setup
# world.done()

# Définition des variables des containers
door.value("open", False)
door.value("locked", True)

listener = inputs.Listener()  # Permet de réaliser des actions indépendamment de la boucle principale en fonction des inputs du joueur
listener.on_press(INTERACT, interaction)
listener.on_press(CROUCH, crouch)
listener.start()

mouse = inputs.MouseMotion(scene, CAMERA_MOUSE_LOOK_SPEED_X, CAMERA_MOUSE_LOOK_SPEED_Y)

clocks = RealNgine.game.Clocks()  # Des fonctions qui s'exécutent toutes les x secondes
clocks.add("events", 0.1, scene.handle_events)  # Tous les dixièmes de secondes
clocks.add("interaction_test", 0.1, can_interact)
clocks.add("fps", 1, FPS)

on_interactive = False

t1 = time.perf_counter()  # Utile pour le delta time
fps = 0
fps_count = 0
while scene.exists():
    fps_count += 1
    dt = time.perf_counter() - t1 or MIN_DT
    t1 = time.perf_counter()
    world.compute()  # Calcule toutes les vertexes du monde (à noter que chaque container à un .computed qui contient ses polygones)
    world.render()  # Les affiche à l'écran
    scene.write(f"DT: {round(1000 * dt)}ms", -730, 380)
    scene.write(f"FPS: {fps}", -730, 360)
    scene.write(f"Player x: {round(player.x)}", -730, 340)
    scene.write(f"Player y: {round(player.y)}", -730, 320)
    scene.write(f"Player z: {round(player.z)}", -730, 300)
    scene.write(f"Camera rot x: {round(player.camera.rx * 180 / math.pi)}", -730, 280)
    scene.write(f"Camera rot y: {round(player.camera.ry * 180 / math.pi)}", -730, 260)
    scene.write(f"Camera rot z: {round(player.camera.rz * 180 / math.pi)}", -730, 240)
    radius = CURSOR_MAX_RADIUS if on_interactive else CURSOR_MIN_RADIUS
    scene.dot(0, 0, radius, "#000000")  # Curseur
    scene.update()

    forward_x = math.sin(player.camera.ry) * math.cos(player.camera.rx)
    forward_y = math.sin(player.camera.rx)
    forward_z = math.cos(player.camera.ry) * math.cos(player.camera.rx)

    right_x = math.cos(player.camera.ry)
    right_y = 0
    right_z = -math.sin(player.camera.ry)

    move_x = 0
    move_y = 0
    move_z = 0

    if inputs.is_pressed(FORWARD):
        move_x += forward_x
        move_y += forward_y
        move_z += forward_z

    if inputs.is_pressed(BACKWARD):
        move_x -= forward_x
        move_y -= forward_y
        move_z -= forward_z

    if inputs.is_pressed(RIGHT):
        move_x += right_x
        move_y += right_y
        move_z += right_z

    if inputs.is_pressed(LEFT):
        move_x -= right_x
        move_y -= right_y
        move_z -= right_z

    length = math.hypot(move_x, move_z)
    if length:
        move_x /= length
        move_z /= length
    dx, dy = mouse.displacement()
    ry = dx
    rx = -dy
    player.rz = (inputs.is_pressed("g") - inputs.is_pressed("f")) * math.pi / 6
    player.rotate(rx, ry, 0)
    player.move(move_x * PLAYER_SPEED * dt, 0, move_z * PLAYER_SPEED * dt)
    clocks.check()
