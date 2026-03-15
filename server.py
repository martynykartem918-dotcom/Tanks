import socket, threading, os, time

os.environ['SDL_VIDEODRIVER'] = 'dummy'

class Server:
    def __init__(self, host='localhost', port=8080):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((host, port))
        except Exception as e:
            print(f"Помилка запуску: {e}")
            return
        
        self.server.listen(2)
        self.clients = {}
        self.ready_players = set()
        self.countdown_started = False
        self.lock = threading.Lock()
        print(f"Сервер запущено на {host}:{port}")

    def broadcast(self, msg, exclude_id=None):
        data = (msg + "\n").encode()
        with self.lock:
            for pid, conn in list(self.clients.items()):
                if pid != exclude_id:
                    try:
                        conn.sendall(data)
                    except:
                        self.remove_player(pid)

    def remove_player(self, pid):
        with self.lock:
            if pid in self.clients:
                self.clients[pid].close()
                del self.clients[pid]
            if pid in self.ready_players:
                self.ready_players.remove(pid)

    def start_countdown_logic(self):
        for i in range(5, 0, -1):
            self.broadcast(f"T,{i}")
            print(f"До старту: {i}")
            time.sleep(1)
        
        self.broadcast("START")
        print("ГРУ РОЗПОЧАТО!")
        self.ready_players.clear()
        self.countdown_started = False

    def handle_client(self, conn, pid):
        buffer = ""
        try:
            conn.settimeout(5.0)
            name = conn.recv(1024).decode().strip()
            conn.settimeout(None)
            x, y, angle = (100, 250, 0) if pid % 2 == 0 else (700, 250, 180)
            conn.sendall(f"ID,{pid},{x},{y},{angle}\n".encode())

            while True:
                data = conn.recv(2048).decode(errors="ignore")
                if not data: break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line:
                        continue

                    if line == "READY":
                        self.ready_players.add(pid)
                        print(f"Гравець {pid} готовий!")

                        if len(self.ready_players) >= 2 and not self.countdown_started:
                            self.countdown_started = True
                            threading.Thread(target=self.start_countdown_logic, daemon=True).start()
                    else:
                        self.broadcast(line, exclude_id=pid)

        except Exception as e:
            print(f"Клієнт {pid} відключився: {e}")
        finally:
            self.remove_player(pid)

    def run(self):
        pid_counter = 0
        while True:
            conn, addr = self.server.accept()
            print(f"Нове підключення: {addr} (ID: {pid_counter})")
            with self.lock:
                self.clients[pid_counter] = conn
            
            threading.Thread(target=self.handle_client, args=(conn, pid_counter), daemon=True).start()
            pid_counter += 1

if __name__ == "__main__":
    server = Server()
    server.run()
