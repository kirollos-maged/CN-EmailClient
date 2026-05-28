import socket
import threading


host = '127.0.0.1'
port = 9999


# ==========================================
# Handle Client Notification
# ==========================================
def handle_client(client_socket, client_address):

    try:

        message = client_socket.recv(1024).decode('utf-8')

        print(f"[{client_address}] -> {message}")

        client_socket.close()

    except Exception as e:

        print(f"Client Error: {e}")


# ==========================================
# Start Notification Server
# ==========================================
server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server_socket.bind((host, port))

server_socket.listen()

print("===================================")
print(" Notification Server is Running ")
print("===================================")

print("Waiting for notifications...\n")


while True:

    client_socket, client_address = server_socket.accept()

    # Handle each client in separate thread
    client_thread = threading.Thread(
        target=handle_client,
        args=(client_socket, client_address)
    )

    client_thread.start()