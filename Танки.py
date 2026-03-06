from pygame import *
from math import *
import random

init()
screen_size = 800, 500
screen_width, screen_height = 800, 500
screen = display.set_mode(screen_size)
display.set_caption("Стрілялки")
gun_raw = image.load("gun.png").convert_alpha()
display.set_icon(gun_raw)
clock = time.Clock()

player_name = "ТИ"

font.init()
main_font = font.SysFont("Arial", 26)
small_font = font.SysFont("Arial", 18)
label_font = font.SysFont("Arial", 28, bold=True)

# --- ФУНКЦІЇ ТА КЛАСИ ---

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
        speed_x = random.uniform(-3, 3) # Випадкова швидкість по X
        speed_y = random.uniform(-3, 3) # Випадкова швидкість по Y
        lifetime = random.randint(20, 50) # Випадковий час життя
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
        self.lifetime = lifetime # Як довго частинка живе (в кадрах)
        self.original_lifetime = lifetime

    def update(self):
        # Рух частинки
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1 # Зменшуємо час життя
        
        # Трохи сповільнюємо частинку (тертя)
        self.speed_x *= 0.95
        self.speed_y *= 0.95

    def draw(self, surf):
        # Малюємо частинку (квадратик або коло)
        # Прозорість залежить від часу життя
        alpha = int((self.lifetime / self.original_lifetime) * 255)
        
        # Переконуємося, що alpha в межах 0-255
        if alpha < 0: alpha = 0
        if alpha > 255: alpha = 255
            
        p_surf = Surface((4, 4)) # Розмір частинки
        p_surf.fill(self.color)
        p_surf.set_alpha(alpha)
        
        surf.blit(p_surf, (int(self.x), int(self.y)))

# Спроба завантаження ресурсів
try:
    gun_raw = transform.scale(gun_raw, (100, 65))
    my_gun_base = transform.flip(gun_raw, True, False)
    bullet_img = image.load("bullet.png").convert_alpha()
    bullet_img = transform.scale(bullet_img, (50, 18))
    background = transform.scale(image.load("space.jpg"), screen_size)
except:
    gun_raw = Surface((100, 65), SRCALPHA); draw.polygon(gun_raw, (0, 255, 0), [(0, 0), (100, 32), (0, 65)])
    my_gun_base = transform.flip(gun_raw, True, False)
    bullet_img = Surface((50, 18), SRCALPHA); draw.ellipse(bullet_img, (255, 255, 0), (0, 0, 50, 18))
    background = Surface(screen_size); background.fill((30, 30, 30))

class Bullet:
    def __init__(self, x, y, angle, speed, owner="player",ghost=False):
        self.owner = owner  # Власник кулі (player або enemy)
        self.ghost = ghost
        self.image = transform.rotate(bullet_img, angle)
        self.mask = mask.from_surface(self.image)
        if self.ghost: self.image.set_alpha(150)
        self.rect = self.image.get_rect(center=(x, y))
        rad = radians(angle)
        self.dx = cos(rad) * speed
        self.dy = -sin(rad) * speed
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

class LuckyBlock:
    def __init__(self, blocks, p1_x, p1_y, p2_x, p2_y):
        self.size = 40
        self.rect = Rect(0, 0, self.size, self.size)
        self.mask = mask.Mask((self.size, self.size), fill=True) 
        self.spawn(blocks, p1_x, p1_y, p2_x, p2_y)

    def spawn(self, blocks, p1_x, p1_y, p2_x, p2_y):
        while True:
            self.rect.x = random.randint(50, 750 - self.size)
            self.rect.y = random.randint(50, 450 - self.size)
            hit_wall = any(self.rect.colliderect(b.rect) for b in blocks)
            dist1 = sqrt((self.rect.centerx - p1_x)**2 + (self.rect.centery - p1_y)**2)
            dist2 = sqrt((self.rect.centerx - p2_x)**2 + (self.rect.centery - p2_y)**2)
            if not hit_wall and dist1 > 150 and dist2 > 150: 
                break

    def draw(self, screen):
        draw.rect(screen, (255, 165, 0), self.rect)
        draw.rect(screen, (255, 255, 255), self.rect, 3)
        txt = main_font.render("?", True, (255, 255, 255))
        screen.blit(txt, (self.rect.x + 14, self.rect.y + 5))

Blocks = [
    Block(390, 175, 20, 150, (255, 255, 0)), Block(325, 240, 150, 20, (255, 255, 0)),
    Block(130, 300, 20, 125, (255, 255, 0)), Block(130, 405, 125, 20, (255, 255, 0)),
    Block(650, 75, 20, 125, (255, 255, 0)), Block(545, 75, 125, 20, (255, 255, 0)),
    Block(235, 75, 20, 125, (255, 255, 0)), Block(130, 180, 125, 20, (255, 255, 0)),
    Block(545, 300, 20, 125, (255, 255, 0)), Block(545, 300, 125, 20, (255, 255, 0))
]
# Створюємо червоний блок смерті внизу екрана
death_block = Block(0, 490, 800, 20, (255, 0, 0))
death_block_up = Block(0, -10, 800, 20, (255, 0, 0))

p1_angle = 0
p1_center_x, p1_center_y = 60, 250
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
p1_shield_end = 0
p1_start_pos = (60, 250) # Твоя початкова позиція

base_speed, speed_mod = 4, 1.0
stun_until = shield_until = speed_effect_until = 0
current_effect_text = ""
homing_left = 0
next_homing_time = 0

lucky_obj = None
lucky_spawn_delay = 15000
next_lucky_spawn = time.get_ticks() + 15000 

p2_alive = True
p2_start_pos = (690, 217)
p2_rect = gun_raw.get_rect(topleft=p2_start_pos)
p2_mask = mask.from_surface(gun_raw)
p2_respawn_time = p2_shield_end = p2_stun_until = 0

# Таймери для нових ефектів
inv_ws_until = inv_ad_until = inv_qe_until = ghost_mode_until = 0
is_stuck_in_wall = False
effect_text_until = 0
big_bullet_until = 0

running = True
while running:
    
    current_time = time.get_ticks()
    
    is_stunned = current_time < stun_until
    has_shield = current_time < shield_until
    has_speed = current_time < speed_effect_until
    is_ghost = current_time < ghost_mode_until
    if not has_speed: speed_mod = 1.0

    # Перевірка на активність будь-якого ефекту для спавну лакіблоку
    active_any = (is_stunned or has_shield or has_speed or is_ghost or 
                  current_time < inv_ws_until or current_time < inv_ad_until or 
                  current_time < inv_qe_until or current_time < p2_stun_until)

    if not active_any and lucky_obj is None:
        if next_lucky_spawn == 0:
            next_lucky_spawn = current_time + lucky_spawn_delay
        if current_time >= next_lucky_spawn:
            lucky_obj = LuckyBlock(Blocks, p1_center_x, p1_center_y, p2_rect.centerx, p2_rect.centery)
    elif active_any:
        next_lucky_spawn = 0

    for e in event.get():
        if e.type == QUIT: running = False
        if e.type == KEYDOWN and not is_stunned:
            if e.key == K_SPACE and ammo > 0 and p1_alive:
                if current_time - last_shot_time >= fire_delay:
                    rad = radians(p1_angle)
                    bx = p1_center_x + 50 * cos(rad) - 17.5 * sin(rad)
                    by = p1_center_y - 50 * sin(rad) - 17.5 * cos(rad)

                    # Створюємо кулю з базовою швидкістю 7
                    bullet_speed = 7
                    is_nuke = False

                    # ПЕРЕВІРКА: чи активний ефект ядерної кулі
                    if current_time < big_bullet_until:
                        bullet_speed = 15  # ЗБІЛЬШЕНА ШВИДКІСТЬ
                        is_nuke = True

                    new_bullet = Bullet(bx, by, p1_angle, speed=bullet_speed, owner="player")
                    new_bullet.is_nuclear = is_nuke # Чітко присвоюємо True або False

                    if is_nuke:
                        orig_w, orig_h = new_bullet.image.get_size()
                        new_bullet.image = transform.scale(new_bullet.image, (orig_w * 3, orig_h * 3))
                        new_bullet.rect = new_bullet.image.get_rect(center=(bx, by))
                        new_bullet.mask = mask.from_surface(new_bullet.image)

                    bullets.append(new_bullet)
                    ammo -= 1
                    last_shot_time = last_reload = current_time
    # Регенерація набоїв
    if ammo < max_ammo and current_time - last_reload >= reload_time:
        ammo += 1
        if ammo < max_ammo: last_reload = current_time

    # Відродження ворога
    if not p2_alive and current_time >= p2_respawn_time:
        p2_alive, p2_rect.x, p2_rect.y = True, p2_start_pos[0], p2_start_pos[1]
        p2_shield_end = current_time + 5000

    # Оновлення спрайту гравця та маски
    rotated_img = transform.rotate(my_gun_base, p1_angle)
    if is_ghost: rotated_img.set_alpha(150)
    new_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
    p1_mask = mask.from_surface(rotated_img)

    if not is_stunned and p1_alive:
        keys = key.get_pressed()
        cs = int(base_speed * speed_mod)
        
        # ЛОГІКА ІНВЕРСІЇ КЛАВІШ
        k_up = K_s if current_time < inv_ws_until else K_w
        k_down = K_w if current_time < inv_ws_until else K_s
        k_left = K_d if current_time < inv_ad_until else K_a
        k_right = K_a if current_time < inv_ad_until else K_d
        k_rot_l = K_e if current_time < inv_qe_until else K_q
        k_rot_r = K_q if current_time < inv_qe_until else K_e

        # 1. ПОВОРОТ
        old_angle = p1_angle
        if keys[k_rot_l]: p1_angle += 3
        if keys[k_rot_r]: p1_angle -= 3
        
        rotated_img = transform.rotate(my_gun_base, p1_angle)
        new_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
        p1_mask = mask.from_surface(rotated_img)
        
        # Перевірка межі екрана та стін для повороту
        collision = not screen.get_rect().contains(new_rect)
        if not collision and not is_ghost:
            for b in Blocks:
                # У циклі перевірки колізій танка (for b in Blocks):
                if p1_mask.overlap(b.mask, (b.rect.x - new_rect.x, b.rect.y - new_rect.y)):
                    # Перевіряємо, чи це саме наш блок смерті
                    if b == death_block_up:
                        if current_time > p1_shield_end: # Якщо немає активного щита
                            p1_alive = False
                            p1_respawn_time = current_time + 5000
                            create_particles(p1_center_x, p1_center_y, (255, 0, 0), count=30)
                            p2_score += 1 # Очко ворогу за твою помилку
                    else:
                        collision = True
                        break
        if collision:
            p1_angle = old_angle
            # Важливо: негайно перераховуємо маску назад, 
            # щоб наступний блок (рух) не бачив "помилкової" колізії
            rotated_img = transform.rotate(my_gun_base, p1_angle)
            p1_mask = mask.from_surface(rotated_img)
            new_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))
        # Зберігаємо старі координати перед будь-яким рухом
        start_x, start_y = p1_center_x, p1_center_y

        # Зберігаємо старі координати перед будь-яким рухом
        start_x, start_y = p1_center_x, p1_center_y

        # 1. РУХ ПО ОСІ X
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

        # 2. РУХ ПО ОСІ Y
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
        
        # -----------------------------------------------------------------------
    # 1. Спочатку оновлюємо актуальний rect гравця (на основі його поточних координат)
    p1_current_rect = rotated_img.get_rect(center=(p1_center_x, p1_center_y))

    # 2. Перевірка смерті ГРАВЦЯ від червоного блоку
    if p1_alive and p1_current_rect.colliderect(death_block.rect):
        # Перевіряємо маску для точності (щоб не вмирати, якщо лише порожній кут картинки торкнувся блоку)
        offset = (death_block.rect.x - p1_current_rect.x, death_block.rect.y - p1_current_rect.y)
        if p1_mask.overlap(death_block.mask, offset):
            if current_time > p1_shield_end:
                p1_hp = 0
                p1_alive = False
                p1_respawn_time = current_time + 5000
                p1_center_x, p1_center_y = p1_start_pos 

    # 3. Перевірка смерті ВОРОГА
    if p2_alive and p2_rect.colliderect(death_block.rect):
        if current_time > p2_shield_end:
            score += 1
            p2_alive = False
            p2_respawn_time = current_time + 5000
    # ------------------------------------------------------------------
        
        if p1_alive and p1_current_rect.colliderect(death_block.rect):
            # Оскільки маска тепер оновлюється на початку кадру, overlap спрацює точно
            offset = (death_block.rect.x - p1_current_rect.x, death_block.rect.y - p1_current_rect.y)
            if p1_mask.overlap(death_block.mask, offset):
                if current_time > p1_shield_end:
                    p1_hp = 0
                    p1_alive = False
                    p1_respawn_time = current_time + 5000
                    p1_center_x, p1_center_y = p1_start_pos

    # --- ПЕРЕВІРКА ЛАКІБЛОКУ  ---
    if lucky_obj is not None:
        offset_lucky = (lucky_obj.rect.x - new_rect.x, lucky_obj.rect.y - new_rect.y)
        if p1_mask.overlap(lucky_obj.mask, offset_lucky):
            eff = random.randint(1, 11)
            lucky_obj = None 
            next_lucky_spawn = 0 
            
            if eff == 1:
                inv_ws_until = current_time + 10000
                current_effect_text = "ІНВЕРСІЯ W / S"
            elif eff == 2:
                inv_ad_until = current_time + 10000
                current_effect_text = "ІНВЕРСІЯ A / D"
            elif eff == 3:
                inv_qe_until = current_time + 10000
                current_effect_text = "ІНВЕРСІЯ Q / E"
            elif eff == 4:
                p2_stun_until = current_time + 4000
                current_effect_text = "ВОРОГ ЗАМЕР!"
            elif eff == 5:
                ghost_mode_until = current_time + 10000
                current_effect_text = "РЕЖИМ ПРИВИДА"
            elif eff == 6:
                current_effect_text = "РАДІАЛЬНИЙ УДАР"
                effect_text_until = current_time + 3000 
                for i in range(0, 360, 36):
                    r_rad = radians(i)
                    # Кулі з'являються колом навколо танка
                    bx = p1_center_x + 40 * cos(r_rad)
                    by = p1_center_y - 40 * sin(r_rad)
                    bullets.append(Bullet(bx, by, i, speed=5, ghost=True, owner="player"))
            elif eff == 7:
                speed_mod, speed_effect_until = 1.6, current_time + 7000
                current_effect_text = "ПРИСКОРЕННЯ"
            elif eff == 8:
                shield_until = current_time + 7000
                current_effect_text = "ЩИТ!"
            # НОВІ ЕФЕКТИ:
            elif eff == 9:
                stun_until = current_time + 2000 # Стан гравця на 2 секунди
                current_effect_text = "СТАН!"
            elif eff == 10:
                speed_mod, speed_effect_until = 0.5, current_time + 5000 # Уповільнення
                current_effect_text = "УПОВІЛЬНЕННЯ"
            elif eff == 11:
                current_effect_text = "ЯДЕРНА КУЛЯ!"
                big_bullet_until = current_time + 8000  # Діє 8 секунд
                effect_text_until = current_time + 2000

    # ОБРОБКА КУЛЬ
    for bullet in bullets[:]:
        bullet.update()

        if hasattr(bullet, 'is_nuclear') and bullet.is_nuclear:
            # Створюємо помаранчеві та жовті іскри за кулею
            create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 150, 0), count=2)
        
        # 1. Вихід за межі екрана
        if not screen.get_rect().colliderect(bullet.rect):
            if bullet in bullets: bullets.remove(bullet)
            continue
        
        # 2. Перевірка влучання в стіни
        hit_wall = False
        if not bullet.ghost:
            for b in Blocks:
                if bullet.rect.colliderect(b.rect):
                    # ДОДАЄМО УМОВУ: якщо куля НЕ ядерна, вона вдаряється
                    if not (hasattr(bullet, 'is_nuclear') and bullet.is_nuclear):
                        create_particles(bullet.rect.centerx, bullet.rect.centery, (150, 150, 150), count=5)
                        hit_wall = True
                        break
                    else:
                        # Якщо ядерна — просто лишаємо трохи іскор при прольоті крізь стіну
                        if current_time % 5 == 0: # не кожний кадр, щоб не лагало
                            create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 200, 0), count=2)
        
        if hit_wall:
            if bullet in bullets: bullets.remove(bullet)
            continue # Куля зникла, переходимо до наступної

        # 3. Перевірка влучання у ВОРОГА
        if p2_alive and bullet.owner == "player" and bullet.rect.colliderect(p2_rect):
            # Якщо куля була ядерною — робимо ГІГАНТСЬКИЙ вибух
            p_count = 50 if (hasattr(bullet, 'is_nuclear') and bullet.is_nuclear) else 15
            create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 100, 0), count=p_count)
            
            if current_time > p2_shield_end:
                score += 1
                p2_alive = False
                p2_respawn_time = current_time + 5000
            
            if bullet in bullets: bullets.remove(bullet)
            continue

        # 4. Перевірка влучання у ГРАВЦЯ (тебе)
        if p1_alive and bullet.owner != "player" and bullet.rect.colliderect(new_rect):
            if p1_mask.overlap(bullet.mask, (bullet.rect.x - new_rect.x, bullet.rect.y - new_rect.y)):
                # Колір залежить від щита
                p_color = (0, 255, 255) if current_time < shield_until else (255, 255, 255)
                create_particles(bullet.rect.centerx, bullet.rect.centery, p_color, count=12)
                
                if current_time > p1_shield_end:
                    p1_hp -= 5
                    if p1_hp <= 0:
                        p1_alive = False
                        p1_respawn_time = current_time + 5000
                
                if bullet in bullets: bullets.remove(bullet)
                continue
        

    # --- ОБРОБКА ЧАСТИНОК (в while running, після куль) ---
    for particle in particles[:]:
        particle.update()
        if particle.lifetime <= 0:
            particles.remove(particle)
    
        
        # Перевірка влучання у гравця
        if p1_alive and bullet.owner != "player" and bullet.rect.colliderect(new_rect):
            if p1_mask.overlap(bullet.mask, (bullet.rect.x - new_rect.x, bullet.rect.y - new_rect.y)):
                
                # --- ПЕРЕВІРКА ВЛУЧАННЯ В ЩИТ ---
                # Якщо білий щит (відродження)
                if current_time < p1_shield_end:
                    create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 255, 255), count=10) # Білі частинки
                    if bullet in bullets: bullets.remove(bullet) # Куля зникає
                    continue # Переходимо до наступної кулі
                
                # Якщо блакитний щит (лакіблок)
                elif current_time < shield_until:
                    create_particles(bullet.rect.centerx, bullet.rect.centery, (0, 255, 255), count=10) # Блакитні частинки
                    if bullet in bullets: bullets.remove(bullet) # Куля зникає
                    continue # Переходимо до наступної кулі
                
                # --- Якщо щитів немає (звичайна смерть) ---
                else:
                    create_particles(bullet.rect.centerx, bullet.rect.centery, (50, 255, 50), count=15) # Зелені частинки
        # Додаємо умову: bullet.owner != "player"
        if p1_alive and bullet.owner != "player" and bullet.rect.colliderect(new_rect):
            if p1_mask.overlap(bullet.mask, (bullet.rect.x - new_rect.x, bullet.rect.y - new_rect.y)):
                if current_time > p1_shield_end: # Якщо немає білого щита
                    p1_hp -= 5
                    if p1_hp <= 0:
                        p1_alive = False
                        p1_respawn_time = current_time + 5000
                bullets.remove(bullet)
                continue
    # Відродження гравця
    if not p1_alive and current_time >= p1_respawn_time:
        p1_alive = True
        p1_hp = 5
        p1_center_x, p1_center_y = p1_start_pos
        p1_shield_end = current_time + 5000 # Білий щит на 5 секунд

    # --- МАЛЮВАННЯ ---
    screen.blit(background, (0, 0))
    for b in Blocks: b.draw(screen)
    death_block.draw(screen) 
    death_block_up.draw(screen)
    if lucky_obj: lucky_obj.draw(screen)
    for b in bullets: screen.blit(b.image, b.rect)
    
    # 1. МАЛЮВАННЯ ГРАВЦЯ
    if p1_alive:
        if not is_stunned or (current_time // 200 % 2):
            screen.blit(rotated_img, new_rect)
        if current_time < shield_until: # Блакитний щит
            draw.circle(screen, (0, 255, 255), (int(p1_center_x), int(p1_center_y)), 55, 3)
        if current_time < p1_shield_end: # Білий щит
            draw.circle(screen, (255, 255, 255), (int(p1_center_x), int(p1_center_y)), 60, 3)
        draw_player_label(player_name, label_font, p1_center_x, p1_center_y - 70)
    else:
        rt_p1 = max(0, (p1_respawn_time - current_time) / 1000)
        screen.blit(main_font.render(f"ВИ ВІДРОДИТЕСЬ: {rt_p1:.1f}с", True, (0, 255, 0)), (50, 500))

    # 2. МАЛЮВАННЯ ВОРОГА
    if p2_alive:
        if not (current_time < p2_stun_until and (current_time // 100 % 2)):
            screen.blit(gun_raw, p2_rect)
        if current_time < p2_shield_end:
            draw.circle(screen, (255, 255, 255), p2_rect.center, 60, 3)
    else:
        rt_p2 = max(0, (p2_respawn_time - current_time) / 1000)
        screen.blit(main_font.render(f"ВОРОГ ЗА: {rt_p2:.1f}с", True, (255, 50, 50)), (550, 500))

    # 3. ІНТЕРФЕЙС ТА ЕФЕКТИ
    screen.blit(label_font.render(f"Набої: {ammo}/{max_ammo}", True, (255, 255, 255)), (20, 20))
    screen.blit(label_font.render(f"ОЧКИ: {score}", True, (0, 255, 0)), (20, 440))

    max_end = max(inv_ws_until, inv_ad_until, inv_qe_until, ghost_mode_until, 
                  stun_until, speed_effect_until, shield_until, p2_stun_until, big_bullet_until, effect_text_until)

    if current_time < max_end:
        is_bad = current_time < stun_until or (speed_mod < 1 and current_time < speed_effect_until)
        txt_color = (255, 50, 50) if is_bad else (100, 255, 100)
        draw_center_text(current_effect_text, txt_color)
        time_left = (max_end - current_time) / 1000
        if time_left > 0.1:
            screen.blit(main_font.render(f"ЗАЛИШИЛОСЯ: {time_left:.1f}с", True, txt_color), (320, 20))
    elif lucky_obj is None:
        timer_val = max(0, (next_lucky_spawn - current_time) / 1000)
        screen.blit(main_font.render(f"ДО НОВОГО ЛАКІБЛОКУ: {timer_val:.1f}с", True, (255, 165, 0)), (280, 20))

    # --- МАЛЮВАННЯ ЧАСТИНОК (в while running, перед update) ---
    for particle in particles:
        particle.draw(screen)

    # Очки ворога (справа)
    # screen_width — це ширина твого вікна (наприклад, 800 або 1000)
    p2_score_text = label_font.render(f"ОЧКИ ВОРОГА: {p2_score}", True, (255, 50, 50))
    text_rect = p2_score_text.get_rect(topright=(screen_width - 20, 440))
    screen.blit(p2_score_text, text_rect)
    # Якщо гравець мертвий
    if not p1_alive:
        time_left = max(0, int((p1_respawn_time - current_time) / 1000))
        respawn_text = label_font.render(f"ВИ ЗАГИНУЛИ! Відродження через: {time_left}с", True, (255, 0, 0))
        # Малюємо по центру зверху (y = 60)
        r_rect = respawn_text.get_rect(center=(screen_width // 2, 60))
        screen.blit(respawn_text, r_rect)

    # Якщо ворог мертвий
    if not p2_alive:
        time_p2 = max(0, int((p2_respawn_time - current_time) / 1000))
        p2_death_text = label_font.render(f"ВОРОГ ЗНИЩЕНИЙ! Відродження через: {time_p2}с", True, (0, 255, 0))
        # Малюємо трохи нижче першого повідомлення (y = 90)
        p2_r_rect = p2_death_text.get_rect(center=(screen_width // 2, 90))
        screen.blit(p2_death_text, p2_r_rect)
    # --- ПЕРЕВІРКА СМЕРТІ ВІД БЛОКІВ СМЕРТІ ---
    
    # 1. Перевірка для ГРАВЦЯ (від обох блоків)
    if p1_alive:
        # Перевіряємо зіткнення з нижнім АБО верхнім блоком
        if p1_current_rect.colliderect(death_block.rect) or p1_current_rect.colliderect(death_block_up.rect):
            if current_time > p1_shield_end:
                create_particles(p1_center_x, p1_center_y, (255, 0, 0), count=30)
                p1_alive = False
                p1_respawn_time = current_time + 5000
                p2_score += 1  # НАРАХОВУЄМО ОЧКИ ВОРОГУ
                p1_center_x, p1_center_y = p1_start_pos

    # 2. Перевірка для ВОРОГА (від обох блоків)
    if p2_alive:
        if p2_rect.colliderect(death_block.rect) or p2_rect.colliderect(death_block_up.rect):
            if current_time > p2_shield_end:
                create_particles(p2_rect.centerx, p2_rect.centery, (255, 0, 0), count=30)
                score += 1     # НАРАХОВУЄМО ОЧКИ ТОБІ
                p2_alive = False
                p2_respawn_time = current_time + 5000
    
    

    display.update()
    clock.tick(60)

quit()
