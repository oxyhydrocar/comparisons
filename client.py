#!/usr/bin/env python3
import socket
import sys
import os

HOST = '127.0.0.1'
PORT = 9999

class FileClient:
    def __init__(self, host, port, client_id):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.socket = None

    def connect_and_receive(self):
        """Connect to server and receive file"""
        try:
            # Create socket and connect
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Client {self.client_id}: Connected to server at {self.host}:{self.port}")

            # Receive file size (8 bytes)
            file_size_bytes = self.socket.recv(8)
            if not file_size_bytes:
                print(f"Client {self.client_id}: Connection closed by server")
                return

            file_size = int.from_bytes(file_size_bytes, byteorder='big')
            print(f"Client {self.client_id}: Expecting {file_size} bytes")

            # Receive file data
            received_data = bytearray()
            while len(received_data) < file_size:
                chunk = self.socket.recv(min(4096, file_size - len(received_data)))
                if not chunk:
                    break
                received_data.extend(chunk)

            # Save file
            output_filename = f"received_file_client_{self.client_id}.txt"
            with open(output_filename, 'wb') as f:
                f.write(received_data)

            print(f"Client {self.client_id}: File received and saved as {output_filename} ({len(received_data)} bytes)")

            self.socket.close()

        except ConnectionRefusedError:
            print(f"Client {self.client_id}: Connection refused. Is the server running?")
        except Exception as e:
            print(f"Client {self.client_id}: Error - {e}")
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass

def main():
    # Get client ID from command line argument
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    client = FileClient(HOST, PORT, client_id)
    client.connect_and_receive()

if __name__ == "__main__":
    main()
