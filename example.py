import sqlite3
import hashlib
import base64
import os
import subprocess
import ssl
import requests

# 1. Hardcoded sensitive credentials
DB_USER = "admin"
DB_PASSWORD = "supersecretpassword"

# 2. Insecure use of hashing (MD5 is considered broken for security purposes)
def insecure_hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# 3. SQL Injection vulnerability
def insecure_query(db_conn, user_input):
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    cursor = db_conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

# 4. Insecure use of cryptography (hardcoded encryption key and use of a weak algorithm)
HARDCODED_KEY = b'1234567890123456'  # 16 bytes key (AES-128)
def insecure_encrypt_data(data):
    from Crypto.Cipher import AES
    cipher = AES.new(HARDCODED_KEY, AES.MODE_ECB)  # ECB mode is insecure
    ciphertext = cipher.encrypt(data.ljust(16))  # padding with spaces
    return base64.b64encode(ciphertext)

# 5. Command Injection vulnerability
def insecure_os_command(user_input):
    command = f"ls {user_input}"
    return subprocess.run(command, shell=True, stdout=subprocess.PIPE)

# 6. Insecure SSL handling (ignores certificate validation)
def insecure_ssl_request(url):
    response = requests.get(url, verify=False)  # SSL certificate verification is disabled
    return response.text

# 7. Weak password generation (predictable password)
def generate_weak_password(username):
    return username + "123"  # Weak password pattern

# 8. Using a predictable random number generator for sensitive data
def insecure_random_token():
    return base64.b64encode(os.urandom(8)).decode()  # Insufficient token size for sensitive purposes

# 9. Error handling leaks sensitive information
def insecure_error_handling():
    try:
        1 / 0  # Intentional division by zero
    except Exception as e:
        print(f"An error occurred: {e}")  # Leaks full exception details, useful for attackers

# 10. Using outdated and insecure libraries (example of using an insecure method in a library)
def insecure_ssl_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)  # TLS 1.0 is considered insecure and outdated
    return context

# Example usage of the insecure functions
if __name__ == "__main__":
    conn = sqlite3.connect(':memory:')  # In-memory SQLite database for demonstration
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")

    # Example of SQL Injection
    user_input = "' OR '1'='1"  # SQL Injection payload
    users = insecure_query(conn, user_input)
    print("Fetched users:", users)

    # Example of insecure hash
    print("Insecure hashed password:", insecure_hash_password("password123"))

    # Example of encryption
    print("Encrypted data:", insecure_encrypt_data(b"MySecretData"))

    # Example of command injection
    print("Command output:", insecure_os_command("; rm -rf /"))

    # Example of insecure SSL request
    print("Insecure SSL request:", insecure_ssl_request("https://example.com"))

    # Example of weak password generation
    print("Generated weak password:", generate_weak_password("admin"))

    # Example of insecure random token generation
    print("Insecure random token:", insecure_random_token())

    # Example of insecure error handling
    insecure_error_handling()

    # Example of insecure SSL context
    context = insecure_ssl_context()
    print("Insecure SSL context:", context)
