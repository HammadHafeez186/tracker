import socket
import threading
import json

peer_registry = {}  # peer_id -> (ip, port)
file_registry = {}  # file_name -> set of peer_ids
file_parts = {}     # file_name -> number of parts
valid_tokens = {}   # peer_id -> token

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode()
        msg = json.loads(data)

        if msg['type'] == 'AUTH':
            token = f"token_{msg['peer_id']}"
            valid_tokens[msg['peer_id']] = token
            conn.send(json.dumps({"status": "OK", "token": token}).encode())

        elif msg['type'] == 'REGISTER':
            if valid_tokens.get(msg['peer_id']) != msg['token']:
                conn.send(json.dumps({"status": "FAIL", "reason": "Invalid token"}).encode())
                return

            peer_registry[msg['peer_id']] = (addr[0], msg['port'])

            for fname, total_parts in msg['files'].items():
                if fname not in file_registry:
                    file_registry[fname] = set()
                    file_parts[fname] = total_parts
                file_registry[fname].add(msg['peer_id'])

            conn.send(json.dumps({"status": "REGISTERED"}).encode())
            print(f"[REGISTER] {msg['peer_id']} at {addr[0]}:{msg['port']}")

        elif msg['type'] == 'PEER_LIST':
            if valid_tokens.get(msg['peer_id']) != msg['token']:
                conn.send(json.dumps({"status": "FAIL", "reason": "Invalid token"}).encode())
                return

            peers = file_registry.get(msg['file_name'], set())
            response = [{"peer_id": pid, "ip": peer_registry[pid][0], "port": peer_registry[pid][1]} for pid in peers]
            total = file_parts.get(msg['file_name'], 0)
            conn.send(json.dumps({"peers": response, "total_parts": total}).encode())

    except Exception as e:
        print(f"[TRACKER ERROR] {e}")
    finally:
        conn.close()

def start_tracker(host="0.0.0.0", port=9000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"[TRACKER] Listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_tracker()
