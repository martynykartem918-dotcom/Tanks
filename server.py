from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from time import time, sleep
from random import randint, choice

sock = socket(AF_INET, SOCK_STREAM)
sock.bind(("localhost", 8080))
sock.listen(5)
sock.setblocking(False)

players = {}
scores = {}
id_counter = 0

lucky_block = {
    "active": False,
    'x': 0, 'y': 0, 'eff': 0,
    "next_spawn_time": time() + 5
}

def handle_data():
    while True:
        sleep(0.01)
        current_time = time()

        if not players:
            sleep(0.5)
            continue

        if not lucky_block["active"] and current_time >= lucky_block["next_spawn_time"]:
            while True:
                rx, ry = randint(100, 700), randint(100, 500)
                too_close = False
                for p in players.values():
                    dist = ((p['x'] - rx)**2 + (p['y'] - ry)**2)**0.5
                    if dist < 250:
                        too_close = True
                        break
                if not too_close or not players: break
            
            lucky_block.update({"x": rx, "y": ry, "eff": choice([6, 8, 11]), "active": True})
            msg = f"SPAWN_LB,{rx},{ry},{lucky_block['eff']}"
            for c in list(players.keys()):
                try: c.send(msg.encode())
                except: pass

        for conn in list(players.keys()):
            try:
                data = conn.recv(1024).decode().strip()
                if not data:
                    if conn in players: del players[conn]
                    continue

                if "TAKEN_LB" in data:
                    if lucky_block["active"]:
                        lucky_block["active"], lucky_block["next_spawn_time"] = False, current_time + 10
                        for c in players:
                            try: c.send("DESTROY_LB".encode())
                            except: pass
                    continue

                if "SHOOT" in data:
                    for c in players:
                        if c != conn:
                            try: c.send(data.encode())
                            except: pass
                    continue

                if "KILLED_BY" in data:
                    parts = data.split(',')
                    if len(parts) == 2:
                        killer_id = int(parts[1])
                        scores[killer_id] = scores.get(killer_id, 0) + 1
                        msg = f"SCORE_UPDATE,{killer_id},{scores[killer_id]}"
                        rx, ry = randint(100, 700), randint(100, 500)
                        for c in players:
                            try: 
                                c.send(msg.encode())
                                if players[c]['id'] == players[conn]['id']:
                                    c.send(f"TELEPORT,{rx},{ry}".encode())
                            except: pass
                    continue

                if data.startswith("P,"):
                    parts = data.split(',')
                    if len(parts) == 5:
                        players[conn].update({'x': int(parts[2]), 'y': int(parts[3]), 'angle': int(parts[4])})

            except:
                if conn in players: del players[conn]
                continue

        if players:
            packet = '|'.join([f"{p['id']},{p['x']},{p['y']},{p['angle']},{p['name']}" for p in players.values()])
            for conn in list(players.keys()):
                try: conn.send(packet.encode())
                except: pass

Thread(target=handle_data, daemon=True).start()
print("SERVER started...")

while True:
    try:
        conn, addr = sock.accept()
        conn.setblocking(True)
        name = conn.recv(64).decode().strip()
        if name:
            id_counter += 1
            players[conn] = {'id': id_counter, 'x': 100, 'y': 100, 'angle': 0, 'name': name}
            conn.send(f"{id_counter},100,100,0".encode())
            conn.setblocking(False)
            print(f"ID {id_counter}: {name}")
        else: conn.close()
    except BlockingIOError: sleep(0.1)
    except: pass
