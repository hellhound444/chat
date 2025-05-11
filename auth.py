import hashlib
import os
import re
import ipaddress

USER_FILE = 'users.txt'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def load_users():
    users = {}
    if not os.path.exists(USER_FILE):
        return users
    with open(USER_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) != 3:
                continue
            username, hashed, ip = parts
            users[username] = {'password': hashed, 'ip': ip}
    return users

def register_user():
    username = input("Enter a username: ").strip()
    password = input("Enter a password: ").strip()
    ip_address = input("Enter your IP address: ").strip()

    if not is_valid_ip(ip_address):
        print("Invalid IP address format.")
        return None

    users = load_users()
    if username in users:
        print("Username already exists.")
        return None

    hashed_pw = hash_password(password)
    with open(USER_FILE, 'a') as f:
        f.write(f"{username},{hashed_pw},{ip_address}\n")
    print("Registration successful.")
    return {'username': username, 'ip': ip_address}

def login_user():
    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()
    users = load_users()
    if username not in users:
        print("User not found.")
        return None
    hashed_input = hash_password(password)
    if users[username]['password'] != hashed_input:
        print("Incorrect password.")
        return None
    print("Login successful.")
    return {'username': username, 'ip': users[username]['ip']}
