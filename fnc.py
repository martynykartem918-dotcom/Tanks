from pygame import *
from math import sin, cos, radians

class Block:
    def __init__(self, x, y, width, height, color):
        self.rect = Rect(x, y, width, height)
        self.color = color
    def draw(self, surf):
        draw.rect(surf, self.color, self.rect)



class Particle:
    def __init__(self, x, y, color, speed_x, speed_y, lifetime):
        self.x, self.y = x, y
        self.color = color
        self.speed_x, self.speed_y = speed_x, speed_y
        self.lifetime = self.orig_life = lifetime
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        self.speed_x *= 0.95
        self.speed_y *= 0.95
    def draw(self, surf):
        alpha = max(0, min(255, int((self.lifetime / self.orig_life) * 255)))
        p_surf = Surface((4, 4))
        p_surf.fill(self.color)
        p_surf.set_alpha(alpha)
        surf.blit(p_surf, (int(self.x), int(self.y)))

class Bullet:
    def __init__(self, image, x, y, angle, speed, owner='player'):
        self.image = transform.rotate(image, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = angle
        self.speed = speed
        self.owner = owner
        self.cx, self.cy = float(x), float(y)
        rad = radians(self.angle)
        self.dx = cos(rad) * self.speed
        self.dy = -sin(rad) * self.speed
    def update(self):
        self.cx += self.dx
        self.cy += self.dy
        self.rect.center = (self.cx, self.cy)
