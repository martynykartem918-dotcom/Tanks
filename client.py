from customtkinter import *
from server import host, port
from socket import socket, AF_INET, SOCK_STREAM
from pygame import *
from threading import Thread
from math import sin, cos, radians, sqrt
from random import uniform, randint

launcher = CTk()
launcher.title('Некий лаунчер')
launcher.geometry('300x330')

LABEL = CTkLabel(launcher, text = 'ВХОД В ИГРУ', font = ('Comic Sans MS', 25, 'bold'))
LABEL.pack(pady = 15, padx = 20, anchor = 'center')

name_entry = CTkEntry(launcher, placeholder_text = 'Введите имя 😊', height = 50, font = ('Comic Sans MS', 30))
name_entry.pack(padx = 20, anchor = 'w', fill = 'x')

host_entry = CTkEntry(launcher, placeholder_text = 'Введите хост 😊', height = 50, font = ('Comic Sans MS', 30))
host_entry.insert(0, host)
host_entry.pack(padx = 20, pady = 15, anchor = 'w', fill = 'x')

port_entry = CTkEntry(launcher, placeholder_text = 'Введите порт сервера 😊', height = 50, font = ('Comic Sans MS', 30))
port_entry.insert(0, port)
port_entry.pack(padx = 20, anchor = 'w', fill = 'x')

def click():
    global player_name, host, port
    player_name = name_entry.get()
    host = host_entry.get()
    port = int(port_entry.get())
    launcher.destroy()

start_btn = CTkButton(launcher, text = 'СТАРТ', command = click, height = 50, font = ('Comic Sans MS', 30, 'bold'))
start_btn.pack(pady = 15, padx = 20, fill = 'x')

launcher.mainloop()


init()
mixer.init()
WINDOW_SIZE = [800, 500]
screen = display.set_mode(WINDOW_SIZE)
display.set_caption('Стрелялки')
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
final_font = font.SysFont('Comic Sans MS', 100, bold=True)

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
        if color is None or not (isinstance(color, tuple) or isinstance(color, list) or isinstance(color, Color)):
            self.color = (255, 255, 255)
        else:
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
        if self.lifetime <= 0: return
        alpha = int((self.lifetime / self.original_lifetime) * 255)
        alpha = max(0, min(255, alpha))
        
        p_surf = Surface((4, 4))
        try:
            p_surf.fill(self.color)
        except ValueError:
            p_surf.fill((255, 255, 255))
            
        p_surf.set_alpha(alpha)
        surf.blit(p_surf, (int(self.x), int(self.y)))
gun_raw = transform.flip(gun_raw, True, False)
gun_raw = transform.scale(gun_raw, (100, 65))
bullet_img = image.load('bullet.png').convert_alpha()
bullet_img = transform.scale(bullet_img, (50, 18))
background = transform.scale(image.load('space.jpg'), WINDOW_SIZE)
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
p1_angle = 0
bullets = []
particles = []
ammo, MAX_AMMO = 2, 2
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
    global my_id, p1_center_x, p1_center_y, p1_angle, data_received, game_started, current_effect_text, p1_start_pos, running
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
                    print(f'Мой ID: {my_id}, Позиция: {p1_start_pos}')
                    
                elif msg_type == 'P' and len(parts) >= 7:
                    pid = int(parts[1])
                    if pid != my_id:
                        px, py, pa = int(parts[2]), int(parts[3]), int(parts[4])
                        p_name = parts[5]
                        p_alive_status = int(parts[6])
                        p_shield_status = int(parts[7]) if len(parts) >= 8 else 0
                        all_players_dict[pid] = [pid, px, py, pa, p_name, p_alive_status, p_shield_status]


                elif msg_type == 'B' and len(parts) >= 5:
                    try:
                        bx = float(parts[1])
                        by = float(parts[2])
                        ba = float(parts[3])
                        bn = int(parts[4])
                        
                        is_ghost_bullet = False
                        if len(parts) >= 6:
                            is_ghost_bullet = (int(parts[5]) == 1)
                            
                        is_nuke = (bn == 1)
                        bullet_speed = 7
                        if is_nuke: bullet_speed = 15
                        if is_ghost_bullet: bullet_speed = 0.5
                        
                        enemy_bullet = Bullet(bullet_img, bx, by, ba, speed=bullet_speed, ghost=is_ghost_bullet, owner='enemy')
                        
                        if is_nuke:
                            enemy_bullet.is_nuclear = True
                            orig_w, orig_h = enemy_bullet.image.get_size()
                            enemy_bullet.image = transform.scale(enemy_bullet.image, (orig_w*3, orig_h*3))
                            enemy_bullet.rect = enemy_bullet.image.get_rect(center=(bx, by))
                            enemy_bullet.mask = mask.from_surface(enemy_bullet.image)
                            
                        bullets.append(enemy_bullet)
                    except (ValueError, IndexError):
                        continue

                elif msg_type == 'T':
                    countdown_value = parts[1]
                    current_effect_text = f'ИГРА НАЧНЁТСЯ ЧЕРЕЗ: {countdown_value}'

                elif msg_type == 'D':
                    pass
                    
        except Exception as e:
            print(f'Ошибка получения данных: {e}')
            running = False
            break


game_started = False
recv_thread = Thread(target=receive_data, daemon=True)
recv_thread.start()

ready_sent = False
waiting = True
data_arrival_time = None 
is_ready = False

while waiting:
    screen.blit(background, (0, 0))
    mouse.set_cursor(SYSTEM_CURSOR_ARROW)
    current_time = time.get_ticks()
    
    btn_rect = Rect(300, 250, 200, 60)
    mouse_pos = mouse.get_pos()

    if data_received and data_arrival_time is None:
        data_arrival_time = current_time

    if not data_received or (data_arrival_time and current_time - data_arrival_time < 7000):
        dots = "." * (int(current_time / 300) % 4)
        draw_center_text(f'ПОЛУЧЕНИЕ ДАННЫХ ОТ СЕРВЕРА{dots}', (200, 200, 200))
    
    else:
        if 'ИГРА НАЧНЁТСЯ ЧЕРЕЗ' in current_effect_text:
            draw_center_text(current_effect_text, (255, 255, 0))
        else:
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
            
            if not is_ready:
                btn_text = 'ГОТОВО'
            else:
                dots = "." * (int(current_time / 300) % 4)
                btn_text = f'ЖДЁМ{dots}'
            txt = main_font.render(btn_text, True, (255, 255, 255))
            screen.blit(txt, (btn_rect.centerx - txt.get_width()//2, btn_rect.centery - txt.get_height()//2))

    if game_started and data_received:
        waiting = False

    for e in event.get():
        if e.type == QUIT:
            running = False
            waiting = False
        
        if e.type == MOUSEBUTTONDOWN and e.button == 1:
            if data_arrival_time and (current_time - data_arrival_time >= 3000):
                if not is_ready and btn_rect.collidepoint(e.pos):
                    is_ready = True
                    try:
                        sock.send('READY\n'.encode())
                    except:
                        pass

    display.update()
    clock.tick(30)

mouse.set_cursor(SYSTEM_CURSOR_ARROW)

mixer.music.stop()
mixer.music.load('game_music.mp3')
mixer.music.set_volume(0.07)
mixer.music.play(-1)
lucky_spawn_delay = 15000
next_lucky_spawn = time.get_ticks() + 15000 
game_state = 'playing'
winner = None

while running:
    if game_state == 'playing':
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
                if e.type == KEYDOWN and not is_stunned:
                    if e.key == K_SPACE and ammo > 0 and p1_alive:
                        if current_time - last_shot_time >= fire_delay:
                            rad = radians(p1_angle)
                            angle_norm = p1_angle % 360
                            
                            side_offset = -17.5
                            if 90 < angle_norm < 270:
                                side_offset = 17.5 
                        
                            bx = p1_center_x + 50 * cos(rad) + side_offset * sin(rad)
                            by = p1_center_y - 50 * sin(rad) + side_offset * cos(rad)
                            
                            bullet_speed = 15 if has_nuke_shot else 7
                            is_nuke = has_nuke_shot
                            has_nuke_shot = False 
                            
                            new_bullet = Bullet(bullet_img, bx, by, p1_angle, speed=bullet_speed, owner='player')
                            new_bullet.is_nuclear = is_nuke
                            if is_nuke:
                                orig_w, orig_h = new_bullet.image.get_size()
                                new_bullet.image = transform.scale(new_bullet.image, (orig_w * 3, orig_h * 3))
                                new_bullet.rect = new_bullet.image.get_rect(center=(bx, by))
                                new_bullet.mask = mask.from_surface(new_bullet.image)
                            
                            bullets.append(new_bullet)
                            
                            nuke_val = 1 if is_nuke else 0
                            msg_bullet = f'B,{bx},{by},{p1_angle},{nuke_val},0\n'
                            try: sock.send(msg_bullet.encode())
                            except: pass
                            
                            ammo -= 1
                            last_shot_time = last_reload = current_time

        if ammo < MAX_AMMO and current_time - last_reload >= reload_time:
            ammo += 1
            if ammo < MAX_AMMO: last_reload = current_time

        if not is_stunned and p1_alive:
            keys = key.get_pressed()
            cs = int(base_speed * speed_mod)

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
                temp_base = transform.flip(gun_raw, False, True)
            else:
                temp_base = gun_raw

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
                    temp_base = transform.flip(gun_raw, False, True)
                else:
                    temp_base = gun_raw
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
            
        if lucky_obj is not None:
            offset_lucky = (lucky_obj.rect.x - new_rect.x, lucky_obj.rect.y - new_rect.y)
            if p1_mask.overlap(lucky_obj.mask, offset_lucky):
                eff = 9
                lucky_obj = None 
                next_lucky_spawn = 0 
                if eff == 1:
                    inv_ws_until = current_time + 10000
                    current_effect_text = 'ИНВЕРСИЯ W / S'
                elif eff == 2:
                    inv_ad_until = current_time + 10000
                    current_effect_text = 'ИНВЕРСИЯ A / D'
                elif eff == 3:
                    inv_qe_until = current_time + 10000
                    current_effect_text = 'ИНВЕРСИЯ Q / E'
                elif eff == 4:
                    current_effect_text = 'МНОГО ПУЛЬ!'
                    effect_text_until = current_time + 1000  
                    NUM_BULLETS = 12
                    ANGLE_STEP = 360.0 / NUM_BULLETS 
                    for i in range(NUM_BULLETS):
                        current_angle = i * ANGLE_STEP
                        r_rad = radians(current_angle)
                        bx = p1_center_x + (40 * cos(r_rad))
                        by = p1_center_y - (40 * sin(r_rad))
                        
                        new_b = Bullet(bullet_img, bx, by, current_angle, speed=0.5, ghost=True, owner='player')
                        bullets.append(new_b)
                    
                        msg_bullet = f'B,{bx},{by},{current_angle},0,1\n' 
                        try:
                            sock.send(msg_bullet.encode())
                        except:
                            pass
                elif eff == 5:
                    speed_mod, speed_effect_until = 1.6, current_time + 7000
                    current_effect_text = 'УСКОРЕНИЕ'
                elif eff == 6:
                    stun_until = current_time + 2000
                    current_effect_text = 'СТАН!'
                elif eff == 7:
                    speed_mod, speed_effect_until = 0.7, current_time + 5000
                    current_effect_text = 'ЗАМЕДЛЕНИЕ!'
                elif eff == 8:
                    current_effect_text = 'ЯДЕРНАЯ ПУЛЯ!'
                    has_nuke_shot = True
                    effect_text_until = current_time + 2000
                elif eff == 9:
                    current_effect_text = 'НИЧЕГО!'
                    effect_text_until = current_time + 3000

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
                            create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 255, 0), count=6)
                            hit_wall = True
                            break
                        else:
                            if current_time % 5 == 0:
                                create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 255, 0), count=6)
            if hit_wall:
                if bullet in bullets: bullets.remove(bullet)
                continue

            if bullet.owner == 'player':
                for p_id, p_info in all_players_dict.items():
                    if p_id != my_id and p_info[5] == 1:
                        ex, ey, ea = p_info[1], p_info[2], p_info[3]
                        is_shielded = p_info[6] if len(p_info) >= 7 else 0
                        
                        dist_to_enemy = sqrt((bullet.rect.centerx - ex)**2 + (bullet.rect.centery - ey)**2)

                        if is_shielded and dist_to_enemy <= 70:
                            create_particles(bullet.rect.centerx, bullet.rect.centery, (155, 155, 155), count=8)
                            if bullet in bullets: bullets.remove(bullet)
                            break

                        enemy_ang_n = ea % 360
                        enemy_surf = transform.flip(gun_raw, False, True) if 90 < enemy_ang_n < 270 else gun_raw
                        rot_enemy = transform.rotate(enemy_surf, ea)
                        enemy_rect_tmp = rot_enemy.get_rect(center=(ex, ey))
                        enemy_mask_tmp = mask.from_surface(rot_enemy)
                        offset_bullet = (enemy_rect_tmp.x - bullet.rect.x, enemy_rect_tmp.y - bullet.rect.y)

                        if bullet.mask.overlap(enemy_mask_tmp, offset_bullet):
                            score += 1
                            try: 
                                sock.send(f'D,{p_id}\n'.encode())
                            except: 
                                pass
                            
                            p_count = 60 if getattr(bullet, 'is_nuclear', False) else 15
                            create_particles(bullet.rect.centerx, bullet.rect.centery, (155, 155, 155), count = p_count)
                            if bullet in bullets: bullets.remove(bullet)
                            break

            elif bullet.owner != 'player' and p1_alive:
                dist_to_me = sqrt((bullet.rect.centerx - p1_center_x)**2 + (bullet.rect.centery - p1_center_y)**2)
                
                if current_time < p1_shield_until and dist_to_me <= 70:
                    create_particles(bullet.rect.centerx, bullet.rect.centery, (0, 255, 255), count = 10)
                    if bullet in bullets:
                        bullets.remove(bullet)
                    continue

                offset_me = (bullet.rect.x - new_rect.x, bullet.rect.y - new_rect.y)
                if p1_mask.overlap(bullet.mask, offset_me):
                    p1_hp -= 5
                    if p1_hp <= 0:
                        p1_alive = False
                        p1_respawn_time = current_time + 5000
                        p2_score += 1
                        sock.send(f'P,{my_id},{int(p1_center_x)},{int(p1_center_y)},{int(p1_angle)},{player_name},0\n'.encode())
                    
                    create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 150, 150), count = 12)
                    if bullet in bullets:
                        bullets.remove(bullet)

        if not p1_alive and current_time >= p1_respawn_time:
            p1_alive = True
            p1_hp = 5
            p1_center_x, p1_center_y = p1_start_pos
            p1_shield_until = current_time + 5000
            current_effect_text = 'ЩИТ'
            effect_text_until = current_time + 5000

        screen.blit(background, (0, 0))
        for b in Blocks: 
            b.draw(screen)
        if lucky_obj: 
            lucky_obj.draw(screen)
        for b in bullets: 
            screen.blit(b.image, b.rect)
        for particle in particles[:]:
            particle.draw(screen)
            particle.update()
            if particle.lifetime <= 0: 
                particles.remove(particle)
        if p1_alive:
            if not is_stunned or (current_time // 200 % 2):
                screen.blit(rotated_img, new_rect)
            if current_time < p1_shield_until:
                draw.circle(screen, (255, 255, 255), (int(p1_center_x), int(p1_center_y)), 60, 3)
            draw_player_label(player_name, label_font, p1_center_x, p1_center_y - 70)
        for p_info in list(all_players_dict.values()):
            if len(p_info) < 6: continue 
            p_id, px, py, pa, p_name, is_alive = p_info[0:6]
            is_shielded = p_info[6] if len(p_info) >= 7 else 0
            
            if p_id != my_id:
                if is_alive == 1:
                    p2_alive = True
                    ang_n = pa % 360
                    enemy_base = transform.flip(gun_raw, False, True) if 90 < ang_n < 270 else gun_raw
                    rot_p2 = transform.rotate(enemy_base, pa)
                    p2_rect_current = rot_p2.get_rect(center=(px, py))
                    screen.blit(rot_p2, p2_rect_current)
                    
                    if is_shielded:
                        draw.circle(screen, (0, 255, 255), (px, py), 60, 3)
                    draw_player_label(p_name, label_font, px, py - 70)
                else:
                    if p2_alive:
                        p2_alive = False
                        p2_respawn_time = current_time + 5000
        screen.blit(label_font.render(f'СНАРЯДЫ: {ammo}/{MAX_AMMO}', True, (255, 255, 255)), (20, 20))
        screen.blit(label_font.render(f'ОЧКИ: {score}', True, (0, 255, 0)), (20, 440))
        p2_score_text = label_font.render(f'ОЧКИ ВРАГА: {p2_score}', True, (255, 50, 50))
        screen.blit(p2_score_text, p2_score_text.get_rect(topright=(WINDOW_SIZE[0] - 20, 440)))
        max_end = max(inv_ws_until, inv_ad_until, inv_qe_until, ghost_mode_until, stun_until, speed_effect_until, p1_shield_until, p2_stun_until, effect_text_until)
        if current_time < max_end:
            is_bad = current_time < stun_until or (speed_mod < 1 and current_time < speed_effect_until)
            txt_color = (255, 50, 50) if is_bad else (100, 255, 100)
            draw_center_text(current_effect_text, txt_color)
            time_left = (max_end - current_time) / 1000
            if time_left > 0.1:
                timer_text = main_font.render(f'ЭФФЕКТ {time_left:.2f}с', True, txt_color)
                screen.blit(timer_text, (WINDOW_SIZE[0] // 2 - timer_text.get_width() // 2, 20))
        elif lucky_obj is None:
            timer_val = max(0, (next_lucky_spawn - current_time) / 1000)
            lb_timer = main_font.render(f'ДО НОВОГО ЛАКИБЛОКА: {timer_val:.2f}с', True, (255, 165, 0))
            screen.blit(lb_timer, (WINDOW_SIZE[0] // 2 - lb_timer.get_width() // 2, 20))
        if not p1_alive:
            rt_p1 = max(0, int((p1_respawn_time - current_time) / 1000))
            resp_text = label_font.render(f'ВОЗРОЖДЕНИЕ: {rt_p1}с', True, (0, 255, 0))
            screen.blit(resp_text, resp_text.get_rect(center=(WINDOW_SIZE[0] // 2, 60)))
        if not p2_alive:
            rt_p2 = max(0, int((p2_respawn_time - current_time) / 1000))
            p2_dead_text = label_font.render(f'ВОЗРОЖДЕНИЕ ВРАГА: {rt_p2}', True, (255, 0, 0))
            screen.blit(p2_dead_text, p2_dead_text.get_rect(center=(WINDOW_SIZE[0] // 2, 500 - 60)))
            if current_time >= p2_respawn_time:
                p2_alive = True
                p2_shield_end = current_time + 5000
        if score == 3:
            winner = True
            game_state = 'over'
        elif p2_score == 3:
            winner = False
            game_state = 'over'

        try:
            shield_active = 1 if (current_time < p1_shield_until or current_time < shield_until) else 0
            alive_val = 1 if p1_alive else 0
            msg = f'P,{my_id},{int(p1_center_x)},{int(p1_center_y)},{int(p1_angle)},{player_name},{alive_val},{shield_active}\n'
            sock.send(msg.encode())
        except:
            pass

    elif game_state == 'over':
        for e in event.get():
            if e.type == QUIT:
                running = False
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False
        screen.blit(background, (0, 0))
    
        overlay = Surface(WINDOW_SIZE)
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        if winner:
            txt = final_font.render('ПОБЕДА', True, (0, 150, 255))
        elif not winner:
            txt = final_font.render('ПОРАЖЕНИЕ', True, (255, 50, 50))
        
        text_rect = txt.get_rect(center=(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2))
        screen.blit(txt, text_rect)

        hint = main_font.render('Нажми ESC для выхода', True, (200, 200, 200))
        screen.blit(hint, (WINDOW_SIZE[0]//2 - hint.get_width()//2, WINDOW_SIZE[1]//2 + 80))

    display.update()
    clock.tick(60)

sock.close()
quit()
import sys
sys.exit()
