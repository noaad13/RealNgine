from .engine import Polygon3d, Container3d
from . import __install_package
import subprocess
import math
import time
import ast
import sys
try:
    from lxml import etree as ET
except:
    __install_package("lxml")
    from lxml import etree as ET


# Comment créer un modèle en XML:
# <container>
#    - ID (obligatoire): nom du container, tu peux pas en mettre deux identiques sous le même parents sinon les paths seront identitques
#    - x, y, z (0 par défaut): position par défaut du container dans le monde
#    - px, py, pz (0 par défaut): décalage du modèle par rapport à sa position (pour décaler le centre de rotation par ex)
#    - rx, ry, rz (0 par défaut): rotation par défaut du container
#    - sx, sy, sz (1 par défaut): agrandissement du modèle
#    - interactive (0 par défaut): indique au jeu si le container et ses enfants peuvent être pris ou utilisé
#    - no-culling (0 par défaut)
#    - reverse-culling (0 par défaut) inverse l'ordre des sommets de tous les polygones enfants du container
#
# <poly>
#    - vertices: liste de tuples (x, y, z) qui représentent les sommets d'un polygone (essaie de faire des triangles si possible)
#    - x, y, z: positions du polygone par rapport au centre du modèle
#    - rx, ry, rz: rotations du polygone sur lui-même
#    - color: couleur en hexadécimal
#    - bx: contours du polygone (seulement en CPU=False pour l'instant)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_from_xml(f_path, debug=False, disable_warnings=False):  # Retourne l'objet container
    t1 = time.perf_counter()
    tree = ET.parse(f_path)
    root = tree.getroot()
    paths = []

    def build(node, path, inherit_values=None):
        if inherit_values is None:
            inherit_values = {}  # Les paramètres qui se transmettent de parent à enfant.
            # Ex: si un parent est agrandi 10 fois alors ses enfants grandiront aussi
        c_id = node.get("id", "")
        if not c_id:
            raise ValueError(f"Line {node.sourceline} : A container must have an id") from None
        if path:
            parents = path.split(".")
            path += "." + c_id
            if path in paths:
                if not disable_warnings:
                    print(f"\033[93m[+] '{f_path}' - Line {node.sourceline} : A container named {path} already exists."
                          f"\n    This may lead to ambiguous id resolutions in the future."
                          f"\n    To disable this warning, please use disable_warnings=False\033[00m")
            else:
                paths.append(path)
        else:
            parents = []
            path = c_id

        interactive = int(node.get("interactive", 0)) or inherit_values.get("interactive", False)  # Indique au jeu si l'objet est interactif (taille du curseur)
        no_culling = int(node.get("no-culling", 0)) or inherit_values.get("no-culling", False)  # Ignore le back-face culling
        reverse_culling = int(node.get("reverse-culling", 0)) or inherit_values.get("reverse-culling", False)  # Inverse l'ordre des sommets (donc inverse la face visible)
        sx, sy, sz = float(node.get("sx", 1)), float(node.get("sy", 1)), float(node.get("sz", 1))  # Agrandissements x, y et z

        isx, isy, isz = inherit_values.get("scale", [1, 1, 1])
        scale = [isx * sx, isy * sy, isz * sz]

        # Mise à jour des variables héritables
        inherit_values["interactive"] = interactive
        inherit_values["no-culling"] = no_culling
        inherit_values["reverse-culling"] = reverse_culling
        inherit_values["scale"] = scale

        obj = Container3d(
            # px, py, pz servent à décaler simplement le model sans avoir à réécrire tous les points
            (float(node.get("x", 0)) + float(node.get("px", 0))) * scale[0],
            (float(node.get("y", 0)) + float(node.get("py", 0))) * scale[1],
            (float(node.get("z", 0)) + float(node.get("pz", 0))) * scale[2],
            # rotations par défaut de l'objet
            math.radians(float(node.get("rx", 0))),
            math.radians(float(node.get("ry", 0))),
            math.radians(float(node.get("rz", 0))),
            interactive,
            path  # Ex: table.lamp.bulb
        )
        obj.parents = parents
        for child in node:
            if child.tag == "container":
                obj.children.append(build(child, path, inherit_values.copy()))  # Copie du dict pour éviter un partage entre différentes descendances
            elif child.tag == "poly":
                color = hex_to_rgb(child.get("color", "#FFFFFF"))
                vertexes = ast.literal_eval(child.get("vertices"))
                if reverse_culling:
                    vertexes.reverse()
                for i, p in enumerate(vertexes):
                    vertexes[i] = (p[0] * scale[0], p[1] * scale[1], p[2] * scale[2])
                poly = Polygon3d(
                    vertexes,
                    float(child.get("x", 0)) * scale[0],
                    float(child.get("y", 0)) * scale[1],
                    float(child.get("z", 0)) * scale[2],
                    math.radians(float(child.get("rx", 0))),
                    math.radians(float(child.get("ry", 0))),
                    math.radians(float(child.get("rz", 0))),
                    color,
                    int(child.get("bw", 0)),  # borderwidth: pas encore appliqué au rendu avec Z-buffer
                    no_culling=no_culling
                )
                poly.parents = parents + [c_id]
                obj.children.append(poly)
        return obj
    perf = round((time.perf_counter() - t1)*1000000) / 1000000
    if debug:
        print(f"\033[92m[+] Container '{f_path}' loaded in {perf*1000}ms\033[00m")
    return build(root, "")
