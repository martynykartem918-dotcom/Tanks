from pygame import *

# ===================== PYGAME =====================

init()
screen_size = 800, 500
screen = display.set_mode(screen_size)
clock = time.Clock()

# -------- КЛАСИ --------

class Block:
    def __init__(self, x, y, width, height, color):
        self.rect = Rect(x, y, width, height)
        self.color = color
    def draw(self, screen):
        draw.rect(screen, self.color, self.rect)

# -------- НАЛАШТУВАННЯ ПЕРЕД ЦИКЛОМ --------

# Блоки
Blocks = [
    Block(390, 175, 20, 150, (255, 255, 0)),
    Block(325, 240, 150, 20, (255, 255, 0)),
    Block(130, 300, 20, 125, (255, 255, 0)),
    Block(130, 405, 125, 20, (255, 255, 0)),
    Block(650, 75, 20, 125, (255, 255, 0)),
    Block(545, 75, 125, 20, (255, 255, 0)),
    Block(235, 75, 20, 125, (255, 255, 0)),
    Block(130, 180, 125, 20, (255, 255, 0)),
    Block(545, 300, 20, 125, (255, 255, 0)),
    Block(545, 300, 125, 20, (255, 255, 0))
]
background = image.load("space.webp")
background = transform.scale(background, (screen_size))

running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

    screen.blit(background, (0, 0))

    for blocks in Blocks:
        blocks.draw(screen)

    display.update()
    clock.tick(60)
quit()
