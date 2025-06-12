import socket
import threading
import json

file_registry = {}
lock = threading.Lock()

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode()
        if not data:
            return

        parts = data.strip().split('|')
        cmd = parts[0]

        if cmd == "REGISTER":
            peer_id, port, files_json = parts[1], int(parts[2]), parts[3]
            file_list = json.loads(files_json)
            with lock:
                for file in file_list:
                    if file not in file_registry:
                        file_registry[file] = []
                    entry = {"peer_id": peer_id, "ip": addr[0], "port": port}
                    if entry not in file_registry[file]:
                        file_registry[file].append(entry)
            conn.sendall(b"REGISTERED")

        elif cmd == "PEER_LIST":
            file_name = parts[1]
            with lock:
                peers = file_registry.get(file_name, [])
            conn.sendall(json.dumps(peers).encode())

        else:
            conn.sendall(b"INVALID_COMMAND")
    except Exception as e:
        print(f"[TRACKER ERROR] {e}")
    finally:
        conn.close()

def start_tracker(host='127.0.0.1', port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"[TRACKER] Listening on {host}:{port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_tracker()
