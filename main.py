from RealNgine import inputs, models, init, game, render
import math
import time

def interaction():  # Quand "E" est pressé
    global door
    global key
    global player
    hit = world.what_is_cursor_on()
    if not hit:
        print("no hit")
        return
    if world.is_parent(hit, "house.wall1.door") and door.average_z < INTERACT_RANGE:
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
    elif world.is_parent(hit, "house.nightstand.drawer.key"):
        key.hidden = True
        player.new_item("key")
    elif world.is_parent(hit, "house.nightstand.drawer"):
        drawer = world.find("house.nightstand.drawer")
        if drawer.value("open"):
            drawer.z = 10
            drawer.value("open", False)
        else:
            drawer.z = 32
            drawer.value("open", True)

def crouch():  # Quand shift est pressé
    global player
    if player.crouched:
        player.cam_y = CAMERA_PLAYER_OFF_Y
    else:
        player.cam_y = CAMERA_PLAYER_OFF_Y - 30
    player.move(0, 0, 0)
    player.crouched = not player.crouched

def cursor_hit():  # Te dis si l'objet que tu regardes à un parent interactif
    global on_interactive
    global selected
    hit = world.what_is_cursor_on()
    if all((hit, selected)) and hit != selected[0]:
        selected[0].color = selected[1]
        selected = None
    if not hit:
        on_interactive = False
        return
    if not selected or hit != selected[0]:
        selected = (hit, hit.color)
        color = hit.color
        if not GPU:
            color = models.hex_to_rgb(color)
        color = int(color[0] * 0.96), int(color[1] * 0.96), int(color[2] * 0.96)
        hit.color = color if GPU else models.rgb_to_hex(color)
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
INTERACT_RANGE = 100
PLAYER_SPEED = 200
CAMERA_KEYBOARD_LOOK_SPEED = 2
CAMERA_MOUSE_LOOK_SPEED_X = 0.01
CAMERA_MOUSE_LOOK_SPEED_Y = 0.01
CAMERA_PLAYER_OFF_X = 0
CAMERA_PLAYER_OFF_Y = 110
CAMERA_PLAYER_OFF_Z = 0

# Curseur
CURSOR_MIN_RADIUS = 2
CURSOR_MAX_RADIUS = 4

init(GPU)

selected = None

player = game.Player(0, 0, 0, 0, 0, 0, CAMERA_PLAYER_OFF_X, CAMERA_PLAYER_OFF_Y, CAMERA_PLAYER_OFF_Z, 0, 0, 0)  # Le joueur a une caméra par défaut
player.camera.focal_lenght = CAMERA_FOCAL_LENGHT

# --- Containers import ---

key = models.load_from_xml("models/key.xml", debug=True, rgb=GPU)
house = models.load_from_xml("models/house.xml", debug=True, rgb=GPU)
door = models.load_from_xml("models/door.xml", debug=True, rgb=GPU)
bed = models.load_from_xml("models/bed.xml", debug=True, rgb=GPU)
nightstand = models.load_from_xml("models/nightstand.xml", debug=True, rgb=GPU)

if GPU:
    scene = render.PygameScene()
else:
    scene = render.TurtleScene()

# Ton container monde unique
world = game.World(scene, player.camera, auto_update=False, resolution=RES)

# Ajout des containers au monde (pas besoin d'inclure key puisqu'il fait partie de table)
world.containers += [house]

# --- Configuration des containers ---
house.new_children(nightstand)
house.new_children(bed)
nightstand_drawer = world.find("house.nightstand.drawer")
nightstand_drawer.new_children(key)  # Key fait partie de la table
house.children[0].new_children(door)
key.rx = math.pi / 2
key.x = -10
key.y = 10
bed.x = -350
bed.z = -350
nightstand.x = -450
nightstand.z = -400

# Définition des variables des containers
door.value("open", False)
door.value("locked", True)
nightstand_drawer.value("open", False)

listener = inputs.Listener()  # Permet de réaliser des actions indépendamment de la boucle principale en fonction des inputs du joueur
listener.on_press(INTERACT, interaction)
listener.on_press(CROUCH, crouch)
listener.start()

mouse = inputs.MouseMotion(scene, CAMERA_MOUSE_LOOK_SPEED_X, CAMERA_MOUSE_LOOK_SPEED_Y)

clocks = game.Clocks()  # Des fonctions qui s'exécutent toutes les x secondes
clocks.add("events", 0.1, scene.handle_events)  # Tous les dixièmes de secondes
# clocks.add("interaction_test", 0.1, cursor_hit)
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
