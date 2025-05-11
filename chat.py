import socket
import threading
import hashlib
from crypto_utils import generate_keypair, encrypt_message, decrypt_message

MSG_LOG = 'msg.txt'
my_public_key, my_private_key = generate_keypair()

def log_message(sender, recipient, message):
    checksum = hashlib.sha256(message.encode()).hexdigest()
    with open(MSG_LOG, 'a') as f:
        f.write(f"{sender}->{recipient}: {message} [SHA256: {checksum}]\n")

def verify_checksum(message, checksum):
    return hashlib.sha256(message.encode()).hexdigest() == checksum

def handle_client(conn, addr, my_username):
    try:
        print(f"[Incoming] Connection from {addr}")
        decision = input("Accept chat? (yes/no): ").strip().lower()
        if decision != 'yes':
            conn.send("REJECT".encode())
            conn.close()
            return

        conn.send("ACCEPT".encode())
        conn.send(f"{my_public_key[0]},{my_public_key[1]}".encode())
        their_key_raw = conn.recv(1024).decode()
        their_public_key = tuple(map(int, their_key_raw.split(',')))
        start_chat(conn, their_public_key, my_private_key, my_username, "Peer")

    except Exception as e:
        print(f"[!] Error in connection: {e}")
        conn.close()

def start_server(my_username, my_ip):
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((my_ip, 12345))
        server.listen(5)
        print(f"[Server] Listening on {my_ip}:12345...")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr, my_username)).start()
    except Exception as e:
        print(f"[Server Error] {e}")

def connect_to_peer(target_ip, my_username, peer_username):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((target_ip, 12345))

        response = client.recv(1024).decode()
        if response != "ACCEPT":
            print("Chat request was rejected.")
            client.close()
            return

        their_key_raw = client.recv(1024).decode()
        their_public_key = tuple(map(int, their_key_raw.split(',')))
        client.send(f"{my_public_key[0]},{my_public_key[1]}".encode())

        start_chat(client, their_public_key, my_private_key, my_username, peer_username)

    except Exception as e:
        print(f"[Connect Error] {e}")

def start_chat(conn, their_public_key, my_private_key, my_username, peer_username):
    def receive():
        while True:
            try:
                raw = conn.recv(4096).decode()
                if not raw:
                    break
                parts = raw.split('||')
                if len(parts) != 2:
                    print("[Warning] Message format corrupted!")
                    continue
                encrypted, checksum = parts
                decrypted = decrypt_message(my_private_key, encrypted)
                if verify_checksum(decrypted, checksum):
                    print(f"[{peer_username}]: {decrypted}")
                    log_message(peer_username, my_username, decrypted)
                else:
                    print(f"[Warning] Tampered message from {peer_username}!")
            except:
                break

    def send():
        while True:
            try:
                msg = input()
                if msg.lower() == 'exit':
                    conn.close()
                    break
                encrypted = encrypt_message(their_public_key, msg)
                checksum = hashlib.sha256(msg.encode()).hexdigest()
                conn.send(f"{encrypted}||{checksum}".encode())
                log_message(my_username, peer_username, msg)
            except:
                print("[Error] Could not send message.")
                break

    threading.Thread(target=receive, daemon=True).start()
    send()
