from pygame import *
from math import *

init()
screen_size = 800, 500
screen = display.set_mode(screen_size)
clock = time.Clock()

player_name = "Гравець 1"

font.init()
main_font = font.SysFont("Arial", 26)
small_font = font.SysFont("Arial", 18)
label_font = font.SysFont("Arial", 28, bold=True)

class Block:
    def __init__(self, x, y, width, height, color):
        self.rect = Rect(x, y, width, height)
        self.color = color
    def draw(self, screen):
        draw.rect(screen, self.color, self.rect)

class Bullet:
    def __init__(self, x, y, angle):
        self.image = transform.rotate(bullet_img, angle)
        self.rect = self.image.get_rect(center=(x, y))
        rad = radians(angle)
        self.dx = cos(rad) * 12
        self.dy = -sin(rad) * 12
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

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

gun_raw = image.load("gun.png").convert_alpha()
gun_raw = transform.scale(gun_raw, (100, 65))
my_gun_base = transform.flip(gun_raw, True, False)
gun_mask_base = mask.from_surface(my_gun_base)
bullet_img = image.load("bullet.png").convert_alpha()
bullet_img = transform.scale(bullet_img, (50, 18))
background = transform.scale(image.load("space.jpg"), screen_size)

p1_angle = 0
p1_center_x, p1_center_y = 60, 250
bullets = []
ammo = 2
max_ammo = 2
reload_time = 750 
last_reload = time.get_ticks()
fire_delay = 80 
last_shot_time = 0
score = 0

base_speed = 4
current_speed = base_speed
speed_boost_end = 0

p2_alive = True
p2_start_pos = (690, 217)
p2_rect = gun_raw.get_rect(x=p2_start_pos[0], y=p2_start_pos[1])
p2_respawn_time = 0
p2_shield_end = 0

screen_rect = Rect(0, 0, 800, 500)
rotate_speed = 3

def draw_player_label(text, font, x, y):
    text_surf = font.render(text, True, (0, 0, 0))
    tw, th = text_surf.get_size()
    padding = 6
    bg_rect = Rect(x - tw//2 - padding, y - th//2 - padding, tw + padding*2, th + padding*2)
    draw.rect(screen, (255, 255, 255), bg_rect)
    draw.rect(screen, (0, 0, 0), bg_rect, 2)
    screen.blit(text_surf, (x - tw//2, y - th//2))

running = True
while running:
    current_time = time.get_ticks()
    
    if current_time < speed_boost_end:
        current_speed = base_speed * 1.5
    else:
        current_speed = base_speed

    for e in event.get():
        if e.type == QUIT:
            running = False
        if e.type == KEYDOWN:
            if e.key == K_SPACE and ammo > 0:
                if current_time - last_shot_time >= fire_delay:
                    rad = radians(p1_angle)
                    dist, side = 45, 17
                    spawn_x = p1_center_x + dist * cos(rad) - side * sin(rad)
                    spawn_y = p1_center_y - dist * sin(rad) - side * cos(rad)
                    bullets.append(Bullet(spawn_x, spawn_y, p1_angle))
                    ammo -= 1
                    last_shot_time = current_time
                    if ammo == max_ammo - 1: last_reload = current_time

    if ammo < max_ammo and current_time - last_reload >= reload_time:
        ammo += 1
        if ammo < max_ammo: last_reload = current_time

    if not p2_alive and current_time >= p2_respawn_time:
        p2_alive = True
        p2_rect.x, p2_rect.y = p2_start_pos
        p2_shield_end = current_time + 5000

    keys = key.get_pressed()
    old_x, old_y, old_angle = p1_center_x, p1_center_y, p1_angle
    if keys[K_q]: p1_angle += rotate_speed
    if keys[K_e]: p1_angle -= rotate_speed
    if keys[K_w]: p1_center_y -= current_speed
    if keys[K_s]: p1_center_y += current_speed
    if keys[K_a]: p1_center_x -= current_speed
    if keys[K_d]: p1_center_x += current_speed

    rotated_img = transform.rotate(my_gun_base, p1_angle)
    new_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
    gun_mask = mask.from_surface(rotated_img)

    collision = not screen_rect.contains(new_rect)
    for b in Blocks:
        offset = (b.rect.x - new_rect.x, b.rect.y - new_rect.y)
        block_mask = mask.Mask((b.rect.width, b.rect.height), True)
        if gun_mask.overlap(block_mask, offset):
            collision = True
    if collision:
        p1_center_x, p1_center_y, p1_angle = old_x, old_y, old_angle
        rotated_img = transform.rotate(my_gun_base, p1_angle)
        new_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))

    for bullet in bullets[:]:
        bullet.update()
        if not screen_rect.colliderect(bullet.rect):
            bullets.remove(bullet)
            continue
        
        hit = False
        for b in Blocks:
            if bullet.rect.colliderect(b.rect): hit = True
        
        if p2_alive and bullet.rect.colliderect(p2_rect):
            if current_time > p2_shield_end:
                score += 1
                p2_alive = False
                p2_respawn_time = current_time + 5000
                speed_boost_end = current_time + 3000
            hit = True 
            
        if hit: bullets.remove(bullet)

    screen.blit(background, (0, 0))
    for b in Blocks: b.draw(screen)
    for bullet in bullets: screen.blit(bullet.image, bullet.rect)
    screen.blit(rotated_img, new_rect)

    if p2_alive:
        screen.blit(gun_raw, p2_rect)
        if current_time < p2_shield_end:
            draw.rect(screen, (255, 255, 255), p2_rect.inflate(10, 10), 3)
    else:
        respawn_in = max(0, (p2_respawn_time - current_time) / 1000)
        resp_text = small_font.render(f"Відродження: {respawn_in:.1f}с", True, (255, 100, 100))
        screen.blit(resp_text, (p2_start_pos[0], p2_start_pos[1]))

    draw_player_label(player_name, label_font, p1_center_x, p1_center_y - 70)
    
    screen.blit(main_font.render(f"Набої: {ammo}/{max_ammo}", True, (255, 255, 255)), (20, 20))
    if ammo < max_ammo:
        tl = max(0, (reload_time - (current_time - last_reload)) / 1000)
        screen.blit(small_font.render(f"До нового: {tl:.2f}с", True, (200, 200, 200)), (20, 50))
    
    screen.blit(main_font.render(f"ОЧКИ: {score}", True, (255, 255, 255)), (20, 440))
    
    if current_time < speed_boost_end:
        boost_in = (speed_boost_end - current_time) / 1000
        boost_text = small_font.render(f"ШВИДКІСТЬ +50%: {boost_in:.1f}с", True, (100, 255, 100))
        screen.blit(boost_text, (20, 470))

    display.update()
    clock.tick(60)
quit()
