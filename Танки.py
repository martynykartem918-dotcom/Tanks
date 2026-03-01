from pygame import *

init()
screen_size = 900, 500
screen = display.set_mode(screen_size)
clock = time.Clock()

running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False
    screen.fill((255, 255, 255))
    
    draw.rect(screen, (0, 0, 0), (0, 0, 900, 500), 5)
    display.update()
    clock.tick(60)
quit()