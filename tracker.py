# tracker/tracker.py

import socket
import threading
import json

# Store peer info: { file_name: [ {peer_id, ip, port}, ... ] }
file_registry = {}
lock = threading.Lock()

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode()
        if not data:
            return

        command_parts = data.strip().split('|')
        cmd = command_parts[0]

        if cmd == "REGISTER":
            peer_id, port, files_json = command_parts[1], int(command_parts[2]), command_parts[3]
            file_list = json.loads(files_json)

            with lock:
                for file_name in file_list:
                    if file_name not in file_registry:
                        file_registry[file_name] = []
                    # Avoid duplicate entry
                    peer_entry = {"peer_id": peer_id, "ip": addr[0], "port": port}
                    if peer_entry not in file_registry[file_name]:
                        file_registry[file_name].append(peer_entry)

            conn.sendall(b"REGISTERED")

        elif cmd == "PEER_LIST":
            file_name = command_parts[1]
            with lock:
                peers = file_registry.get(file_name, [])
            conn.sendall(json.dumps(peers).encode())

        else:
            conn.sendall(b"INVALID_COMMAND")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def start_tracker(host='127.0.0.1', port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"[TRACKER] Listening on {host}:{port}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()

if __name__ == "__main__":
    start_tracker()
