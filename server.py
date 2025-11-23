#!/usr/bin/env python3
import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 9999
MAX_CONNECTIONS = 100
FILE_TO_SHARE = 'sample_file.txt'

class FileServer:
    def __init__(self, host, port, max_connections, file_path):
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.file_path = file_path
        self.clients = []
        self.clients_lock = threading.Lock()
        self.server_socket = None

    def start(self):
        """Start the server and wait for connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_connections)

        print(f"Server started on {self.host}:{self.port}")
        print(f"Waiting for {self.max_connections} connections...")

        # Accept connections until we reach max_connections
        for i in range(self.max_connections):
            client_socket, client_address = self.server_socket.accept()
            with self.clients_lock:
                self.clients.append(client_socket)
            print(f"Connection {i + 1}/{self.max_connections} from {client_address}")

        print(f"\nAll {self.max_connections} connections received!")
        print("Starting parallel file transfer...")

        # Share file to all clients in parallel
        self.share_file_parallel()

    def send_file_to_client(self, client_socket, client_index):
        """Send file to a single client"""
        try:
            # Read the file
            with open(self.file_path, 'rb') as f:
                file_data = f.read()

            # Send file size first
            file_size = len(file_data)
            client_socket.sendall(file_size.to_bytes(8, byteorder='big'))

            # Send file data
            client_socket.sendall(file_data)

            print(f"Client {client_index + 1}: File sent successfully ({file_size} bytes)")

            # Close connection
            client_socket.close()

        except Exception as e:
            print(f"Client {client_index + 1}: Error - {e}")
            try:
                client_socket.close()
            except:
                pass

    def share_file_parallel(self):
        """Share file to all connected clients in parallel using threads"""
        threads = []

        with self.clients_lock:
            for i, client_socket in enumerate(self.clients):
                thread = threading.Thread(
                    target=self.send_file_to_client,
                    args=(client_socket, i)
                )
                threads.append(thread)
                thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        print("\nFile transfer completed for all clients!")
        self.server_socket.close()

def main():
    # Check if file exists
    if not os.path.exists(FILE_TO_SHARE):
        print(f"Error: {FILE_TO_SHARE} not found!")
        print("Please create the file first or modify FILE_TO_SHARE variable.")
        return

    server = FileServer(HOST, PORT, MAX_CONNECTIONS, FILE_TO_SHARE)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    main()
