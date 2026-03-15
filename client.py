from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from pygame import *
from math import sin, cos, radians, sqrt
from random import uniform, randint
import menu

launcher = menu.Menu()
launcher.mainloop()
player_name, port, host = launcher.name, launcher.port, launcher.host

init()
mixer.init()
screen = display.set_mode((800, 500))
display.set_caption('Стрілялки')
gun_raw = image.load('gun.png').convert_alpha()
display.set_icon(gun_raw)
clock = time.Clock()
mixer.music.load('menu_music.mp3')
mixer.music.set_volume(0.07)
mixer.music.play(-1)

font.init()
main_font = font.SysFont('Arial', 26)
small_font = font.SysFont('Arial', 18)
label_font = font.SysFont('Arial', 28, bold=True)
win_or_lose_font = font.Font("Comic Sans MS", 85, bold=True)
win_or_lose_color = None
win_or_lose_until = None

def draw_win_or_lose(text, win_or_lose_color):
    if not text:
        return

    border_color = (0, 0, 0)
    border_offset = 4
    
    for dx in range(-border_offset, border_offset + 1, border_offset):
        for dy in range(-border_offset, border_offset + 1, border_offset):
            if dx == 0 and dy == 0:
                continue
            
            border_surf = win_or_lose_font.render(text, True, border_color)
            border_rect = border_surf.get_rect(center=(800 // 2 + dx, 500 // 2 + dy))
            screen.blit(border_surf, border_rect)
            
    main_surf = win_or_lose_font.render(text, True, win_or_lose_color)
    main_rect = main_surf.get_rect(center=(800 // 2, 500 // 2))
    screen.blit(main_surf, main_rect)

def draw_player_label(text, font, x, y):
    text_surf = font.render(text, True, (0, 0, 0))
    tw, th = text_surf.get_size()
    padding = 6
    bg_rect = Rect(x - tw//2 - padding, y - th//2 - padding, tw + padding*2, th + padding*2)
    draw.rect(screen, (255, 255, 255), bg_rect)
    draw.rect(screen, (0, 0, 0), bg_rect, 2)
    screen.blit(text_surf, (x - tw//2, y - th//2))

def draw_center_text(text, color):
    txt_surf = label_font.render(text, True, color)
    txt_rect = txt_surf.get_rect(center=(400, 150))
    bg_rect = txt_rect.inflate(20, 10)
    draw.rect(screen, (0, 0, 0), bg_rect)
    draw.rect(screen, color, bg_rect, 2)
    screen.blit(txt_surf, txt_rect)

def create_particles(x, y, color, count=10):
    for _ in range(count):
        speed_x = uniform(-3, 3)
        speed_y = uniform(-3, 3)
        lifetime = randint(20, 50)
        particles.append(Particle(x, y, color, speed_x, speed_y, lifetime))

class Block:
    def __init__(self, x, y, width, height, color):
        self.rect = Rect(x, y, width, height)
        self.color = color
        self.mask = mask.Mask((width, height), fill=True)
    def draw(self, screen):
        draw.rect(screen, self.color, self.rect)

class Particle:
    def __init__(self, x, y, color, speed_x, speed_y, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.lifetime = lifetime
        self.original_lifetime = lifetime

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        self.speed_x *= 0.95
        self.speed_y *= 0.95

    def draw(self, surf):
        alpha = int((self.lifetime / self.original_lifetime) * 255)
        if alpha < 0: alpha = 0
        if alpha > 255: alpha = 255
        p_surf = Surface((4, 4))
        p_surf.fill(self.color)
        p_surf.set_alpha(alpha)
        surf.blit(p_surf, (int(self.x), int(self.y)))
gun_raw = transform.flip(gun_raw, True, False)
gun_raw = transform.scale(gun_raw, (100, 65))
my_gun_base = gun_raw
bullet_img = image.load('bullet.png').convert_alpha()
bullet_img = transform.scale(bullet_img, (50, 18))
background = transform.scale(image.load('space.jpg'), (800, 500))
class Bullet:
    def __init__(self, image, x, y, angle, speed, ghost=False, owner='player'):
        self.original_image = image
        self.image = transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = angle
        self.speed = speed
        self.ghost = ghost
        self.owner = owner
        self.center_x = float(x)
        self.center_y = float(y)
        rad = radians(self.angle)
        self.dx = cos(rad) * self.speed
        self.dy = -sin(rad) * self.speed
        self.mask = mask.from_surface(self.image)
    def update(self):
        self.center_x += self.dx
        self.center_y += self.dy
        self.rect.center = (self.center_x, self.center_y)
class LuckyBlock:
    def __init__(self, blocks, p1_x, p1_y, p2_x, p2_y):
        self.size = 40
        self.rect = Rect(0, 0, self.size, self.size)
        self.mask = mask.Mask((self.size, self.size), fill=True) 
        self.spawn(blocks, p1_x, p1_y, p2_x, p2_y)
    def spawn(self, blocks, p1_x, p1_y, p2_x, p2_y):
        while True:
            self.rect.x = randint(50, 750 - self.size)
            self.rect.y = randint(50, 450 - self.size)
            hit_wall = any(self.rect.colliderect(b.rect) for b in blocks)
            dist1 = sqrt((self.rect.centerx - p1_x)**2 + (self.rect.centery - p1_y)**2)
            dist2 = sqrt((self.rect.centerx - p2_x)**2 + (self.rect.centery - p2_y)**2)
            if not hit_wall and dist1 > 150 and dist2 > 150: 
                break
    def draw(self, screen):
        draw.rect(screen, (255, 165, 0), self.rect)
        draw.rect(screen, (255, 255, 255), self.rect, 3)
        txt = main_font.render('?', True, (255, 255, 255))
        screen.blit(txt, (self.rect.x + 14, self.rect.y + 5))
Blocks = [
    Block(390, 175, 20, 150, (255, 255, 0)), Block(325, 240, 150, 20, (255, 255, 0)),
    Block(130, 300, 20, 125, (255, 255, 0)), Block(130, 405, 125, 20, (255, 255, 0)),
    Block(650, 75, 20, 125, (255, 255, 0)), Block(545, 75, 125, 20, (255, 255, 0)),
    Block(235, 75, 20, 125, (255, 255, 0)), Block(130, 180, 125, 20, (255, 255, 0)),
    Block(545, 300, 20, 125, (255, 255, 0)), Block(545, 300, 125, 20, (255, 255, 0))
]
lose = False
win = False
death_block = Block(0, 490, 800, 20, (255, 0, 0))
death_block_up = Block(0, -10, 800, 20, (255, 0, 0))
p1_angle = 0
bullets = []
particles = []
ammo, max_ammo = 2, 2
reload_time, fire_delay = 750, 80
last_reload = last_shot_time = time.get_ticks()
score = 0
p2_score = 0
p2_hp = 5
p1_hp = 5
p1_alive = True
p1_respawn_time = 0
p1_shield_until = 0
has_nuke_shot = False
base_speed, speed_mod = 4, 1.0
stun_until = shield_until = speed_effect_until = 0
current_effect_text = ''
homing_left = 0
next_homing_time = 0
lucky_obj = None
p2_alive = True
p2_start_pos = (690, 217)
p2_rect = gun_raw.get_rect(topleft=p2_start_pos)
p2_mask = mask.from_surface(gun_raw)
p2_respawn_time = p2_shield_end = p2_stun_until = 0
inv_ws_until = inv_ad_until = inv_qe_until = ghost_mode_until = 0
is_stuck_in_wall = False
effect_text_until = 0
big_bullet_until = 0
sock = socket(AF_INET, SOCK_STREAM)
sock.connect((host, port))
sock.setblocking(True)
sock.sendall(f'{player_name}\n'.encode())

running = True
game_started = False
data_received = True
all_players_dict = {}
all_players = []
scores = {}
data_received = False
game_started = False

def receive_data():
    global my_id, p1_center_x, p1_center_y, p1_angle, data_received, game_started, current_effect_text, p1_start_pos, running, win_or_lose_text, win_or_lose_color, win_or_lose_until
    while running:
        try:
            data_bytes = sock.recv(4096)
            if not data_bytes: 
                running = False
                break

            decoded_data = data_bytes.decode()
            lines = decoded_data.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line: 
                    continue
                if line == 'START':
                    game_started = True
                    continue
                
                parts = line.split(',')
                msg_type = parts[0]

                if msg_type == 'ID':
                    my_id = int(parts[1])
                    p1_center_x = int(parts[2])
                    p1_center_y = int(parts[3])
                    p1_angle = int(parts[4])
                    p1_start_pos = (p1_center_x, p1_center_y)
                    data_received = True 
                    print(f'Мій ID: {my_id}, Позиція: {p1_start_pos}')
                    
                if msg_type == 'P' and len(parts) >= 7:
                    pid = int(parts[1])
                    if pid != my_id:
                        px, py, pa = int(parts[2]), int(parts[3]), int(parts[4])
                        p_name = parts[5]
                        p_alive_status = int(parts[6])
                        all_players_dict[pid] = [pid, px, py, pa, p_name, p_alive_status]


                elif msg_type == 'B' and len(parts) >= 5:
                    try:
                        bx, by = float(parts[1]), float(parts[2])
                        ba, bn = float(parts[3]), int(parts[4])
                        is_nuke = (bn == 1)
                    
                        enemy_bullet = Bullet(bullet_img, bx, by, ba, speed=15 if is_nuke else 7, owner='enemy')
                        if is_nuke:
                            enemy_bullet.is_nuclear = True
                            orig_w, orig_h = enemy_bullet.image.get_size()
                            enemy_bullet.image = transform.scale(enemy_bullet.image, (orig_w*3, orig_h*3))
                            enemy_bullet.rect = enemy_bullet.image.get_rect(center=(bx, by))
                            enemy_bullet.mask = mask.from_surface(enemy_bullet.image)
                        bullets.append(enemy_bullet)
                    except ValueError:
                        continue

                elif msg_type == 'T':
                    countdown_value = parts[1]
                    current_effect_text = f'ГРА ПОЧНЕТЬСЯ ЧЕРЕЗ: {countdown_value}'

                elif msg_type == 'D':
                    pass
                elif msg_type == "WIN_DISCONNECT":
                    win_or_lose_text = 'ТЕХНІЧНА ПЕРЕМОГА!'
                    win_or_lose_color = (0, 255, 0)
                    win_or_lose_until = time.get_ticks() + 10000
                    
        except Exception as e:
            print(f'Помилка отримання даних: {e}')
            running = False
            break


game_started = False
recv_thread = Thread(target=receive_data, daemon=True)
recv_thread.start()

is_ready = False
ready_sent = False
waiting = True

while waiting:
    screen.blit(background, (0, 0))
    mouse.set_cursor(SYSTEM_CURSOR_ARROW)

    if not data_received:
        draw_center_text('ОТРИМАННЯ ДАНИХ З СЕРВЕРА...', (200, 200, 200))
    else:
        if 'ГРА ПОЧНЕТЬСЯ' in current_effect_text:
            draw_center_text(current_effect_text, (255, 255, 0))
        else:
            btn_rect = Rect(300, 250, 200, 60)
            mouse_pos = mouse.get_pos()
            is_hovering = btn_rect.collidepoint(mouse_pos)

            if not is_ready:
                if is_hovering:
                    btn_color = (0, 255, 0)
                    mouse.set_cursor(SYSTEM_CURSOR_HAND)
                else:
                    btn_color = (0, 200, 0)
            else:
                btn_color = (100, 100, 100)

            draw.rect(screen, btn_color, btn_rect)
            draw.rect(screen, (255, 255, 255), btn_rect, 2)
            
            btn_text = 'ГОТОВИЙ!' if not is_ready else 'ОЧІКУЄМО...'
            txt = main_font.render(btn_text, True, (255, 255, 255))
            screen.blit(txt, (btn_rect.centerx - txt.get_width()//2, btn_rect.centery - txt.get_height()//2))

    if game_started and data_received:
        waiting = False

    for e in event.get():
        if e.type == QUIT:
            running = False
            waiting = False
        if e.type == MOUSEBUTTONDOWN and data_received and not is_ready:
            if btn_rect.collidepoint(e.pos):
                is_ready = True
                try:
                    sock.send('READY\n'.encode())
                except:
                    pass

    display.update()
    clock.tick(60)

mouse.set_cursor(SYSTEM_CURSOR_ARROW)

mixer.music.stop()
mixer.music.load('game_music.mp3')
mixer.music.set_volume(0.07)
mixer.music.play(-1)
lucky_spawn_delay = 15000
next_lucky_spawn = time.get_ticks() + 15000 
while running:
    current_time = time.get_ticks()
    is_stunned = current_time < stun_until
    has_shield = current_time < shield_until
    has_speed = current_time < speed_effect_until
    is_ghost = current_time < ghost_mode_until
    if not has_speed: speed_mod = 1.0
    active_any = (is_stunned or has_shield or has_speed or is_ghost or 
                  current_time < inv_ws_until or current_time < inv_ad_until or 
                  current_time < inv_qe_until or current_time < p2_stun_until)
    if not active_any and lucky_obj is None:
        if next_lucky_spawn == 0:
            next_lucky_spawn = current_time + lucky_spawn_delay
        if current_time >= next_lucky_spawn:
            lucky_obj = LuckyBlock(Blocks, p1_center_x, p1_center_y, p2_rect.centerx, p2_rect.centery)
    elif active_any: next_lucky_spawn = 0
    for e in event.get():
        if e.type == QUIT: running = False
        if e.type == KEYDOWN and not is_stunned:
            if e.key == K_SPACE and ammo > 0 and p1_alive:
                if current_time - last_shot_time >= fire_delay:
                    rad = radians(p1_angle)
                    bx = p1_center_x + 50 * cos(rad) - 17.5 * sin(rad)
                    by = p1_center_y - 50 * sin(rad) - 17.5 * cos(rad)
                    bullet_speed = 7
                    is_nuke = False
                    if has_nuke_shot:
                        bullet_speed = 15
                        is_nuke = True
                        has_nuke_shot = False 
                        next_lucky_spawn = current_time + lucky_spawn_delay 
                    new_bullet = Bullet(bullet_img, bx, by, p1_angle, speed=bullet_speed, owner='player')
                    new_bullet.is_nuclear = is_nuke
                    if is_nuke:
                        orig_w, orig_h = new_bullet.image.get_size()
                        new_bullet.image = transform.scale(new_bullet.image, (orig_w * 3, orig_h * 3))
                        new_bullet.rect = new_bullet.image.get_rect(center=(bx, by))
                        new_bullet.mask = mask.from_surface(new_bullet.image)
                    bullets.append(new_bullet)
                    nuke_val = 1 if is_nuke else 0
                    msg_bullet = f'B,{bx},{by},{p1_angle},{nuke_val}\n'
                    try: sock.send(msg_bullet.encode())
                    except: pass
                    ammo -= 1
                    last_shot_time = last_reload = current_time

    if ammo < max_ammo and current_time - last_reload >= reload_time:
        ammo += 1
        if ammo < max_ammo: last_reload = current_time

    if not is_stunned and p1_alive and not lose and not win:
        keys = key.get_pressed()
        cs = int(base_speed * speed_mod)
        # ЛОГІКА ІНВЕРСІЇ КЛАВІШ
        k_up = K_s if current_time < inv_ws_until else K_w
        k_down = K_w if current_time < inv_ws_until else K_s
        k_left = K_d if current_time < inv_ad_until else K_a
        k_right = K_a if current_time < inv_ad_until else K_d
        k_rot_l = K_e if current_time < inv_qe_until else K_q
        k_rot_r = K_q if current_time < inv_qe_until else K_e

        old_angle = p1_angle
        if keys[k_rot_l]: p1_angle += 3
        if keys[k_rot_r]: p1_angle -= 3

        angle_norm = p1_angle % 360
        if 90 < angle_norm < 270:
            temp_base = transform.flip(my_gun_base, False, True)
        else:
            temp_base = my_gun_base

        rotated_img = transform.rotate(temp_base, angle_norm)
        new_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
        p1_mask = mask.from_surface(rotated_img)

        collision = not screen.get_rect().contains(new_rect)
            
        if not collision and not is_ghost:
            for b in Blocks:
                offset = (b.rect.x - new_rect.x, b.rect.y - new_rect.y)
                if p1_mask.overlap(b.mask, offset):
                    collision = True
                    break

        if collision:
            p1_angle = old_angle
            angle_norm = p1_angle % 360
            if 90 < angle_norm < 270:
                temp_base = transform.flip(my_gun_base, False, True)
            else:
                temp_base = my_gun_base
            rotated_img = transform.rotate(temp_base, angle_norm)
            p1_mask = mask.from_surface(rotated_img)
            new_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))

        dx = 0
        if keys[k_left]: dx -= cs
        if keys[k_right]: dx += cs
        for _ in range(abs(dx)):
            step = 1 if dx > 0 else -1
            old_rect_x = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
            overlap_before_x = any(p1_mask.overlap(b.mask, (b.rect.x - old_rect_x.x, b.rect.y - old_rect_x.y)) for b in Blocks)
            p1_center_x += step
            new_rect_x = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
            hit = not screen.get_rect().contains(new_rect_x)
            if not hit and not is_ghost:
                overlap_after_x = any(p1_mask.overlap(b.mask, (b.rect.x - new_rect_x.x, b.rect.y - new_rect_x.y)) for b in Blocks)
                if overlap_after_x and not overlap_before_x: hit = True
            if hit:
                p1_center_x -= step
                break

        dy = 0
        if keys[k_up]: dy -= cs
        if keys[k_down]: dy += cs
        for _ in range(abs(dy)):
            step = 1 if dy > 0 else -1
            old_rect_y = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
            overlap_before_y = any(p1_mask.overlap(b.mask, (b.rect.x - old_rect_y.x, b.rect.y - old_rect_y.y)) for b in Blocks)
            p1_center_y += step
            new_rect_y = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
            hit = not screen.get_rect().contains(new_rect_y)
            if not hit and not is_ghost:
                overlap_after_y = any(p1_mask.overlap(b.mask, (b.rect.x - new_rect_y.x, b.rect.y - new_rect_y.y)) for b in Blocks)
                if overlap_after_y and not overlap_before_y: hit = True
            if hit:
                p1_center_y -= step
                break
    p1_current_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
    if p1_alive:
        p1_current_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
        hit_death_block = False
        if p1_current_rect.colliderect(death_block.rect):
            offset = (death_block.rect.x - p1_current_rect.x, death_block.rect.y - p1_current_rect.y)
            if p1_mask.overlap(death_block.mask, offset): hit_death_block = True
        if not hit_death_block and p1_current_rect.colliderect(death_block_up.rect):
            offset_up = (death_block_up.rect.x - p1_current_rect.x, death_block_up.rect.y - p1_current_rect.y)
            if p1_mask.overlap(death_block_up.mask, offset_up): hit_death_block = True
        if hit_death_block:
            if current_time > p1_shield_until:
                create_particles(p1_center_x, p1_center_y, (255, 0, 0), count=30)
                p1_alive = False
                msg_death = f'P,{my_id},{int(p1_center_x)},{int(p1_center_y)},{int(p1_angle)},{player_name},0\n'
                sock.send(msg_death.encode())
                p1_hp = 0
                p1_respawn_time = current_time + 5000
                p2_score += 1
                p1_center_x, p1_center_y = p1_start_pos
    if p2_alive and p2_rect.colliderect(death_block.rect):
        if current_time > p2_shield_end:
            score += 1
            p2_alive = False
            p2_respawn_time = current_time + 5000
    # --- ПЕРЕВІРКА ЛАКІБЛОКУ  ---
    if lucky_obj is not None:
        offset_lucky = (lucky_obj.rect.x - new_rect.x, lucky_obj.rect.y - new_rect.y)
        if p1_mask.overlap(lucky_obj.mask, offset_lucky):
            eff = randint(1, 10)
            lucky_obj = None 
            next_lucky_spawn = 0 
            if eff == 1:
                inv_ws_until = current_time + 10000
                current_effect_text = 'ІНВЕРСІЯ W / S'
            elif eff == 2:
                inv_ad_until = current_time + 10000
                current_effect_text = 'ІНВЕРСІЯ A / D'
            elif eff == 3:
                inv_qe_until = current_time + 10000
                current_effect_text = 'ІНВЕРСІЯ Q / E'
            elif eff == 4:
                p2_stun_until = current_time + 2000
                current_effect_text = 'ВОРОГ ЗАМЕР!'
            elif eff == 5:
                ghost_mode_until = current_time + 10000
                current_effect_text = 'РЕЖИМ ПРИВИДА'
            elif eff == 6:
                current_effect_text = 'РАДІАЛЬНИЙ УДАР'
                effect_text_until = current_time + 1000 
                num_bullets = 16
                angle_step = 360.0 / num_bullets 
                for i in range(num_bullets):
                    current_angle = i * angle_step
                    r_rad = radians(current_angle)
                    bx = p1_center_x + (40 * cos(r_rad))
                    by = p1_center_y - (40 * sin(r_rad))
                    
                    new_b = Bullet(bullet_img, bx, by, current_angle, speed=0.2, ghost=True, owner='player')
                    bullets.append(new_b)
                    
                    # ВІДПРАВКА КОЖНОЇ КУЛІ НА СЕРВЕР
                    msg_bullet = f'B,{bx},{by},{current_angle},0\n'
                    try:
                        sock.send(msg_bullet.encode())
                    except:
                        pass
            elif eff == 7:
                speed_mod, speed_effect_until = 1.6, current_time + 7000
                current_effect_text = 'ПРИСКОРЕННЯ'
            elif eff == 8:
                stun_until = current_time + 2000
                current_effect_text = 'СТАН!'
            elif eff == 9:
                speed_mod, speed_effect_until = 0.5, current_time + 5000
                current_effect_text = 'УПОВІЛЬНЕННЯ'
            elif eff == 10:
                current_effect_text = 'ЯДЕРНА КУЛЯ!'
                has_nuke_shot = True
                effect_text_until = current_time + 2000
    # --- ОБРОБКА КУЛЬ ---
    for bullet in bullets[:]:
        bullet.update()
        if hasattr(bullet, 'is_nuclear') and bullet.is_nuclear: create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 150, 0), count=2)
        if not screen.get_rect().colliderect(bullet.rect):
            if bullet in bullets: bullets.remove(bullet)
            continue

        hit_wall = False
        if not bullet.ghost:
            for b in Blocks:
                if bullet.rect.colliderect(b.rect):
                    if not (hasattr(bullet, 'is_nuclear') and bullet.is_nuclear):
                        create_particles(bullet.rect.centerx, bullet.rect.centery, (150, 150, 150), count=5)
                        hit_wall = True
                        break
                    else:
                        if current_time % 5 == 0:
                            create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 200, 0), count=2)
        if hit_wall:
            if bullet in bullets: bullets.remove(bullet)
            continue

        if bullet.owner == 'player':
            for p_info in all_players:
                p_id, px, py, p_angle, p_name = p_info
                
                rot_p2_tmp = transform.rotate(gun_raw, p_angle)
                p2_rect_tmp = rot_p2_tmp.get_rect(center=(px, py))
                p2_mask_tmp = mask.from_surface(rot_p2_tmp)

                offset_bullet = (p2_rect_tmp.x - bullet.rect.x, p2_rect_tmp.y - bullet.rect.y)
                
                if bullet.mask.overlap(p2_mask_tmp, offset_bullet):
                    try:
                        msg_hit = f'D,{p_id}\n'
                        sock.send(msg_hit.encode())
                    except:
                        pass

                    p_count = 60 if (hasattr(bullet, 'is_nuclear') and bullet.is_nuclear) else 15
                    create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 100, 0), count=p_count)

                    if bullet in bullets:
                        bullets.remove(bullet)
                    break
        if p1_alive and bullet.owner != 'player' and bullet.rect.colliderect(new_rect):
            if p1_mask.overlap(bullet.mask, (bullet.rect.x - new_rect.x, bullet.rect.y - new_rect.y)):
                if current_time < p1_shield_until: p_color = (255, 255, 255)
                elif current_time < shield_until: p_color = (0, 255, 255)
                else: p_color = (50, 255, 50)
                create_particles(bullet.rect.centerx, bullet.rect.centery, p_color, count=12)
                if current_time >= p1_shield_until and current_time >= shield_until:
                    p1_hp -= 5
                    if p1_hp <= 0:
                        p1_alive = False
                        p1_respawn_time = current_time + 5000
                        p2_score += 1
                if bullet in bullets: bullets.remove(bullet)
                continue

    for particle in particles[:]:
        particle.update()
        if particle.lifetime <= 0: particles.remove(particle)

    if not p1_alive and current_time >= p1_respawn_time:
        p1_alive = True
        p1_hp = 5
        p1_center_x, p1_center_y = p1_start_pos
        p1_shield_until = current_time + 5000
        current_effect_text = 'ЩИТ'
        effect_text_until = current_time + 5000

    screen.blit(background, (0, 0))
    for b in Blocks: b.draw(screen)
    death_block.draw(screen) 
    death_block_up.draw(screen)
    if lucky_obj: lucky_obj.draw(screen)
    for b in bullets: screen.blit(b.image, b.rect)
    for particle in particles: particle.draw(screen)
    if p1_alive:
        if not is_stunned or (current_time // 200 % 2):
            screen.blit(rotated_img, new_rect)
        if current_time < p1_shield_until:
            draw.circle(screen, (255, 255, 255), (int(p1_center_x), int(p1_center_y)), 60, 3)
        draw_player_label(player_name, label_font, p1_center_x, p1_center_y - 70)
    for p_info in list(all_players_dict.values()):
        if len(p_info) < 6: 
            continue 
            
        p_id, px, py, pa, p_name, is_alive = p_info
        
        if p_id != my_id and is_alive == 1:
            ang_n = pa % 360
            if 90 < ang_n < 270:
                enemy_base = transform.flip(gun_raw, False, True)
            else:
                enemy_base = gun_raw
            
            rot_p2 = transform.rotate(enemy_base, pa)
            p2_rect_current = rot_p2.get_rect(center=(px, py))
            screen.blit(rot_p2, p2_rect_current)
            
            if current_time < p2_shield_end:
                draw.circle(screen, (0, 255, 255), p2_rect_current.center, 60, 3)
        
            draw_player_label(p_name, label_font, px, py - 70)
    screen.blit(label_font.render(f'НАБОЇ: {ammo}/{max_ammo}', True, (255, 255, 255)), (20, 20))
    screen.blit(label_font.render(f'ОЧКИ: {score}', True, (0, 255, 0)), (20, 440))
    p2_score_text = label_font.render(f'ОЧКИ ВОРОГА: {p2_score}', True, (255, 50, 50))
    screen.blit(p2_score_text, p2_score_text.get_rect(topright=(800 - 20, 440)))
    max_end = max(inv_ws_until, inv_ad_until, inv_qe_until, ghost_mode_until, stun_until, speed_effect_until, p1_shield_until, p2_stun_until, effect_text_until)
    if current_time < max_end:
        is_bad = current_time < stun_until or (speed_mod < 1 and current_time < speed_effect_until)
        txt_color = (255, 50, 50) if is_bad else (100, 255, 100)
        draw_center_text(current_effect_text, txt_color)
        time_left = (max_end - current_time) / 1000
        if time_left > 0.1:
            timer_text = main_font.render(f'ЕФФЕКТ: {time_left:.2f}с', True, txt_color)
            screen.blit(timer_text, (800 // 2 - timer_text.get_width() // 2, 20))
    elif lucky_obj is None:
        timer_val = max(0, (next_lucky_spawn - current_time) / 1000)
        lb_timer = main_font.render(f'ДО НОВОГО ЛАКІБЛОКУ: {timer_val:.2f}с', True, (255, 165, 0))
        screen.blit(lb_timer, (800 // 2 - lb_timer.get_width() // 2, 20))
    if not p1_alive:
        rt_p1 = max(0, int((p1_respawn_time - current_time) / 1000))
        resp_text = label_font.render(f'ВИ ЗАГИНУЛИ! Відродження: {rt_p1}с', True, (255, 0, 0))
        screen.blit(resp_text, resp_text.get_rect(center=(800 // 2, 60)))
    if not p2_alive:
        rt_p2 = max(0, int((p2_respawn_time - current_time) / 1000))
        p2_dead_text = label_font.render(f'ВОРОГ ЗНИЩЕНИЙ! Поява: {rt_p2}', True, (0, 255, 0))
        screen.blit(p2_dead_text, p2_dead_text.get_rect(center=(800 // 2, 500 - 60)))
        if current_time >= p2_respawn_time:
            p2_alive = True
            p2_shield_end = current_time + 5000
    if current_time < win_or_lose_until:
        draw_win_or_lose(win_or_lose_text, win_or_lose_color)

    try:
        alive_val = 1 if p1_alive else 0
        msg = f'P,{my_id},{int(p1_center_x)},{int(p1_center_y)},{int(p1_angle)},{player_name},{alive_val}\n'
        sock.send(msg.encode())
    except:
        pass

    display.update()
    clock.tick(60)

sock.close()
quit()
import sys
sys.exit()
