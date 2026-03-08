import socket, threading, time, random, math
from pygame import Rect

class GameServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(2)
        
        self.lock = threading.Lock()
        self.clients = {}  # {pid: connection}
        self.players = {}  # {pid: {rect, name, hp, score}}
        self.bullets = []  # [{rect, dx, dy, owner_id, is_nuke}]
        
        # Карта: має бути ідентичною клієнту
        self.blocks = [
            Rect(390, 175, 20, 150), Rect(325, 240, 150, 20),
            Rect(130, 300, 20, 125), Rect(130, 405, 125, 20),
            Rect(650, 75, 20, 125), Rect(545, 75, 125, 20),
            Rect(235, 75, 20, 125), Rect(130, 180, 125, 20),
            Rect(545, 300, 20, 125), Rect(545, 300, 125, 20)
        ]
        self.death_zones = [Rect(0, 490, 800, 10), Rect(0, 0, 800, 10)]
        self.lucky_block = None
        self.next_lucky = time.time() + 5
        print(f"📡 Сервер запущено на {host}:{port}")

    def update_physics(self):
        while True:
            start_time = time.time()
            with self.lock:
                # 1. Рух куль
                for b in self.bullets[:]:
                    b['rect'].x += b['dx']
                    b['rect'].y += b['dy']
                    
                    # Перевірка виходу за межі або влучання в блоки
                    if not Rect(0, 0, 800, 500).colliderect(b['rect']) or \
                       any(b['rect'].colliderect(wall) for wall in self.blocks):
                        self.bullets.remove(b)
                        continue
                    
                    # Перевірка влучання в гравців
                    for pid, pdata in self.players.items():
                        if pid != b['owner_id'] and b['rect'].colliderect(pdata['rect']):
                            self.broadcast(f"HIT,{pid},{b['owner_id']}")
                            if b in self.bullets: self.bullets.remove(b)
                
                # 2. Поява Лакі-блоків
                if not self.lucky_block and time.time() > self.next_lucky:
                    lx, ly = random.randint(100, 700), random.randint(100, 400)
                    self.lucky_block = Rect(lx, ly, 40, 40)
                    self.broadcast(f"L,SPAWN,{lx},{ly}")

            # 3. Розсилка стану всіх куль (B_LIST)
            self.broadcast_bullets()
            time.sleep(max(0, 0.016 - (time.time() - start_time)))
    def handle_client(self, conn, pid):
        try:
            name = conn.recv(1024).decode().strip()
            with self.lock:
                self.players[pid] = {"rect": Rect(0, 0, 40, 40), "name": name}
            conn.sendall(f"{pid},100,250,0\n".encode())

            while True:
                data = conn.recv(2048).decode()
                if not data: break
                for line in data.strip().split('\n'):
                    parts = line.split(',')
                    if parts[0] == "P": # Оновлення позиції
                        with self.lock:
                            p = self.players[pid]
                            p['rect'].center = (int(parts[2]), int(parts[3]))
                            # Перевірка смертельних зон
                            if any(p['rect'].colliderect(dz) for dz in self.death_zones):
                                self.broadcast(f"KILL,{pid}")
                            # Перевірка лакі-блоку
                            if self.lucky_block and p['rect'].colliderect(self.lucky_block):
                                self.lucky_block = None
                                self.next_lucky = time.time() + 10
                                self.broadcast(f"L,HIT,{pid},{random.randint(1,5)}")
                        self.broadcast(f"P,{pid},{parts[2]},{parts[3]},{parts[4]},{name}", pid)
                    
                    elif parts[0] == "B": # Нова куля
                        self.create_bullet(pid, parts)
        except: pass
        finally: self.disconnect(pid)
    def create_bullet(self, pid, parts):
        angle = int(parts[3])
        rad = math.radians(angle)
        speed = 15 if parts[4] == "1" else 7
        with self.lock:
            self.bullets.append({
                "rect": Rect(int(parts[1])-5, int(parts[2])-5, 10, 10),
                "dx": math.cos(rad) * speed, "dy": -math.sin(rad) * speed,
                "owner_id": pid, "is_nuke": parts[4] == "1"
            })

    def broadcast_bullets(self):
        if not self.bullets: return
        msg = "B_LIST" + "".join([f",{int(b['rect'].x)},{int(b['rect'].y)},{int(b['is_nuke'])}" for b in self.bullets])
        self.broadcast(msg)

    def broadcast(self, msg, exclude_id=None):
        data = (msg + "\n").encode()
        with self.lock:
            for pid, conn in list(self.clients.items()):
                if pid != exclude_id:
                    try: conn.sendall(data)
                    except: pass

    def disconnect(self, pid):
        with self.lock:
            if pid in self.clients: self.clients[pid].close(); del self.clients[pid]
            if pid in self.players: del self.players[pid]

    def run(self):
        threading.Thread(target=self.update_physics, daemon=True).start()
        pid_cnt = 0
        while True:
            conn, _ = self.server.accept()
            with self.lock: self.clients[pid_cnt] = conn
            threading.Thread(target=self.handle_client, args=(conn, pid_cnt), daemon=True).start()
            pid_cnt += 1

if __name__ == "__main__":
    GameServer().run()
