from . import __install_package

pygame = None
turtle = None
ctypes = None

def init(gpu=False):
    if gpu:
        global pygame
        global ctypes
        try:
            import pygame
        except:
            __install_package("pygame")
            import pygame
        import ctypes
    else:
        global turtle
        import turtle
class TurtleScene:
    def __init__(self):
        self.screen = turtle.Screen()
        self.turtle = turtle.Turtle()
        self.screen.tracer(0, 0)
        self.screen.getcanvas().winfo_toplevel().attributes('-fullscreen', True)
        self.turtle.speed(0)
        self.turtle.hideturtle()

    def handle_events(self):
        pass

    def exists(self):
        try:
            return self.turtle.getcanvas().winfo_exists()
        except:
            return False

    def hide_mouse(self):
        self.screen.getcanvas().config(cursor="none")

    def show_mouse(self):
        self.screen.getcanvas().config(cursor="")

    def fill_polygon(self, points: list[tuple], color, border_width=0, border_color="black"):
        if len(points) < 2:
            return
        self.turtle.goto(*points[0])
        if border_width:
            self.turtle.pensize(border_width)
            self.turtle.color(border_color)
            self.turtle.pendown()
        self.turtle.fillcolor(color)
        self.turtle.begin_fill()
        for i in range(len(points)-1):
            self.turtle.goto(*points[i+1])
        self.turtle.goto(*points[0])
        self.turtle.end_fill()
        self.turtle.penup()

    def write(self, text, x, y, *args, **kwargs):
        self.turtle.penup()
        self.turtle.goto(x, y)
        self.turtle.write(text, *args, **kwargs)

    def draw_pixel(self, x, y, size, color):
        self.turtle.penup()
        self.turtle.goto(x, y)
        self.turtle.dot(size, color)

    def update(self):
        self.screen.update()

    def clear(self):
        self.turtle.clear()

    def dot(self, x, y, radius, color="#000000"):
        self.turtle.penup()
        self.turtle.color(color)
        self.turtle.goto(x, y)
        self.turtle.pendown()
        self.turtle.circle(radius)
        self.turtle.penup()

class PygameScene:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        self.surface = pygame.display.get_surface()
        self.buffer = (ctypes.c_uint8 * (self.width * self.height * 3))()  # Objet partagé avec la dll
        self.zbuffer = (ctypes.c_float * (self.width * self.height))()  # Objet partagé avec la dll
        self.text = []
        self.dots = []
        self.__exists = True

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.__exists = False

    def exists(self):
        return self.__exists

    @staticmethod
    def hide_mouse():
        pygame.mouse.set_visible(False)

    @staticmethod
    def show_mouse():
        pygame.mouse.set_visible(True)

    def clear(self):
        ctypes.memset(self.buffer, 0, self.width * self.height * 3)
        self.zbuffer[:, :] = np.inf

    def write(self, text, x, y, color=(0, 0, 0)):
        self.text.append((text, x, y, color))

    def update(self):
        frame = pygame.image.frombuffer(
            self.buffer,
            (self.width, self.height),
            "RGB"
        )

        self.surface.blit(frame, (0, 0))
        font = pygame.font.SysFont("Arial", 18)
        for t in self.text:
            text, x, y, color = t
            sx = int(x + self.width // 2)
            sy = int(-y + self.height // 2)
            img = font.render(text, True, color)
            self.surface.blit(img, (sx, sy))
        for d in self.dots:
            x, y, r, color = d
            sx = int(x + self.width // 2)
            sy = int(-y + self.height // 2)
            pygame.draw.circle(self.surface, color, (sx, sy), r)
        self.text.clear()
        self.dots.clear()
        pygame.display.flip()

    def dot(self, x, y, r, color=(255, 255, 255)):
        self.dots.append((x, y, r, color))
