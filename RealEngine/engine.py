import math

NEAR_PLANE = 10
MAX_COORD = 5000

def mat4_identity():  # Identité de matrice (EX : identité de multiplication = 1, identité d'addition = 0)
    return [
        [1,0,0,0],
        [0,1,0,0],
        [0,0,1,0],
        [0,0,0,1]
    ]

def mul_mat_vec(m, v):  # Multiplication classique de matrices 4x4
    x, y, z, w = v
    return [
        m[0][0]*x + m[0][1]*y + m[0][2]*z + m[0][3]*w,
        m[1][0]*x + m[1][1]*y + m[1][2]*z + m[1][3]*w,
        m[2][0]*x + m[2][1]*y + m[2][2]*z + m[2][3]*w,
        m[3][0]*x + m[3][1]*y + m[3][2]*z + m[3][3]*w
    ]

def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [
        [1,0,0,0],
        [0,c,-s,0],
        [0,s,c,0],
        [0,0,0,1]
    ]

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [
        [c,0,s,0],
        [0,1,0,0],
        [-s,0,c,0],
        [0,0,0,1]
    ]

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [
        [c,-s,0,0],
        [s,c,0,0],
        [0,0,1,0],
        [0,0,0,1]
    ]

def translate(x, y, z):
    return [
        [1,0,0,x],
        [0,1,0,y],
        [0,0,1,z],
        [0,0,0,1]
    ]

def normalize(v):
    length = math.sqrt(sum(i*i for i in v))
    if length == 0:
        return [0,0,0]
    return [i / length for i in v]

def cross(a, b):  # renvoie un vecteur perpendiculaire aux deux autres
    return [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    ]

def dot(a, b):  # Projette un vecteur sur un axe -> Produit scalaire
    return sum(x*y for x, y in zip(a, b))

def build_view(cam):  # Espace monde -> Espace caméra
    # Rotation 3d yaw et pitch
    forward = normalize([
        math.cos(cam.rx) * math.sin(cam.ry),
        math.sin(cam.rx),
        math.cos(cam.rx) * math.cos(cam.ry)
    ])

    up = [0, 1, 0]

    right = normalize(cross(up, forward))
    up = cross(forward, right)

    # Rotation 2d pour le roll
    cr = math.cos(cam.rz)
    sr = math.sin(cam.rz)

    rolled_right = [
        right[0] * cr - up[0] * sr,
        right[1] * cr - up[1] * sr,
        right[2] * cr - up[2] * sr
    ]

    rolled_up = [
        right[0] * sr + up[0] * cr,
        right[1] * sr + up[1] * cr,
        right[2] * sr + up[2] * cr
    ]

    right = rolled_right
    up = rolled_up

    px, py, pz = cam.x, cam.y, cam.z

    return [
        [right[0], right[1], right[2], -dot(right, [px, py, pz])],
        [up[0], up[1], up[2], -dot(up, [px, py, pz])],
        [forward[0], forward[1], forward[2], -dot(forward, [px, py, pz])],
        [0,0,0,1]
    ]

def mul_mat(a, b):
    r = [[0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            r[i][j] = sum(a[i][k]*b[k][j] for k in range(4))
    return r

def projection(x, y, z, focal_lenght):
    return x * focal_lenght / z, y * focal_lenght / z, z

def intersect(p1, p2, near=0.1):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    t = (near - z1) / (z2 - z1)  # near = z1 + t(z2 - z1)
    x = x1 + (x2 - x1) * t
    y = y1 + (y2 - y1) * t
    z = near
    return x, y, z

def clip_near(p1, p2, near):
    x1, y1, z1, w1 = p1
    x2, y2, z2, w2 = p2
    d1 = z1 / w1
    d2 = z2 / w2
    t = (near - d1) / (d2 - d1)
    x = x1 + (x2 - x1) * t
    y = y1 + (y2 - y1) * t
    z = z1 + (z2 - z1) * t
    w = w1 + (w2 - w1) * t
    return x, y, z, w

def clip_polygon_view(points, near=0.1):
    out = []
    n = len(points)
    for i in range(n):
        curr = points[i]
        prev = points[i - 1]
        curr_depth = curr[2] / curr[3]
        prev_depth = prev[2] / prev[3]
        curr_in = curr_depth > near
        prev_in = prev_depth > near
        if curr_in and prev_in:
            out.append(curr)
        elif prev_in and not curr_in:
            out.append(clip_near(prev, curr, near))
        elif not prev_in and curr_in:
            out.append(clip_near(prev, curr, near))
            out.append(curr)
    return out

def depth(points):
    if not len(points):
        return math.inf
    return sum([p[2] for p in points]) / len(points)

def is_backface(points):
    if len(points) < 3:
        return True
    ax, ay, az = points[0]
    bx, by, bz = points[1]
    cx, cy, cz = points[2]
    abx = bx - ax
    aby = by - ay
    acx = cx - ax
    acy = cy - ay
    nz = abx * acy - aby * acx
    return nz <= 0

class Polygon3d:
    def __init__(self, vertices: list[tuple], x, y, z, rx, ry, rz, color, borderwidth=0, no_culling=False):
        self.vertexes = vertices
        self.x, self.y, self.z = x, y, z
        self.rx, self.ry, self.rz = rx, ry, rz
        self.color = color
        self.borderwidth = borderwidth
        self.no_culling = no_culling
        self.computed = None
        self.parents = []

    @property
    def average_z(self):
        return depth(self.computed)

    def compute(self, camera, parent_matrix):
        Rx = rot_x(self.rx)
        Ry = rot_y(self.ry)
        Rz = rot_z(self.rz)
        T = translate(self.x, self.y, self.z)
        M_local = Rx
        M_local = mul_mat(Ry, M_local)
        M_local = mul_mat(Rz, M_local)
        M_local = mul_mat(T, M_local)
        M_model = mul_mat(parent_matrix, M_local)
        M_view = build_view(camera)
        clip_space = []
        for x, y, z in self.vertexes:
            v = [x, y, z, 1]
            v = mul_mat_vec(M_model, v)
            v = mul_mat_vec(M_view, v)
            clip_space.append(v)
        all_behind = True
        for v in clip_space:
            z = v[2]
            if z > NEAR_PLANE:
                all_behind = False
                break
        if all_behind:
            self.computed = []
            return
        clip_space = clip_polygon_view(clip_space, NEAR_PLANE)
        self.computed = []

        for x, y, z, w in clip_space:
            if abs(w) < 1e-5:
                continue
            inv_w = 1.0 / w
            px = x * inv_w
            py = y * inv_w
            pz = z * inv_w
            sx = x * inv_w
            sy = y * inv_w
            if abs(sx) > MAX_COORD or abs(sy) > MAX_COORD:
                continue
            if pz <= 1:
                continue
            self.computed.append(
                projection(px, py, pz, camera.focal_lenght)
            )
        if is_backface(self.computed) and not self.no_culling:
            self.computed = []

    def duplicate(self):
        return Polygon3d(
            self.vertexes.copy(),
            self.x,
            self.y,
            self.z,
            self.rx,
            self.ry,
            self.rz,
            self.color,
            self.borderwidth,
            no_culling=self.no_culling
        )

class Container3d:
    def __init__(self, x, y, z, rx, ry, rz, interactive, path):
        self.x, self.y, self.z = x, y, z
        self.rx, self.ry, self.rz = rx, ry, rz
        self.children = []
        self.computed = []
        self.values = {}
        self.path = path
        self.parents = None
        self.hidden = False
        self.interactive = interactive

    @property
    def average_z(self):
        total = 0
        for p in self.computed:
            total += p.average_z
        return total / len(self.computed)

    def value(self, k, v=None):
        if v is not None:
            self.values[k] = v
            return
        if k in self.values.keys():
            return self.values[k]

    def compute(self, cam, parent_matrix=None):
        if self.hidden:
            self.computed = []
            return
        if parent_matrix is None:
            parent_matrix = mat4_identity()
        Rx = rot_x(self.rx)
        Ry = rot_y(self.ry)
        Rz = rot_z(self.rz)
        T = translate(self.x, self.y, self.z)
        M_local = mat4_identity()
        M_local = mul_mat(Rx, M_local)
        M_local = mul_mat(Ry, M_local)
        M_local = mul_mat(Rz, M_local)
        M_local = mul_mat(T, M_local)
        M_world = mul_mat(parent_matrix, M_local)
        faces = []
        for child in self.children:
            child.compute(cam, M_world)
            if isinstance(child, Polygon3d):
                if child.computed:
                    faces.append(child)
            elif isinstance(child, Container3d):
                faces.extend(child.computed)
        self.computed = faces

    def duplicate(self, name):
        obj = Container3d(
            self.x,
            self.y,
            self.z,
            self.rx,
            self.ry,
            self.rz,
            name,
            interactive=self.interactive
        )
        obj.values = self.values
        obj.hidden = self.hidden
        for child in self.children:
            obj.children.append(child.duplicate())
        return obj
