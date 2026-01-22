# Client-Server File Sharing Application

A Python-based client-server application that demonstrates parallel file distribution. The server waits for exactly 100 client connections, then broadcasts a file to all connected clients simultaneously using multi-threading.

## Features

- **Connection Pooling**: Server waits for exactly 100 connections before starting file transfer
- **Parallel Distribution**: Uses threading to send files to all clients simultaneously
- **Reliable Transfer**: Includes file size verification and complete data reception
- **Simple Setup**: Easy to configure and test

## Files

- `server.py` - Server application that accepts connections and distributes files
- `client.py` - Client application that connects and receives files
- `sample_file.txt` - Sample file to be shared (can be replaced with any file)
- `launch_clients.sh` - Helper script to launch multiple client instances

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Usage

### Step 1: Start the Server

In terminal 1:
```bash
python3 server.py
```

The server will start and wait for 100 connections.

### Step 2: Launch Clients

In terminal 2, you have two options:

**Option A: Use the helper script (recommended)**
```bash
./launch_clients.sh 100
```

**Option B: Launch clients manually**
```bash
# Launch 100 clients in the background
for i in {1..100}; do python3 client.py $i & done
```

### Step 3: Monitor Progress

The server will display:
- Connection progress (1/100, 2/100, etc.)
- When all connections are received
- File transfer status for each client

Each client will:
- Connect to the server
- Receive the file
- Save it as `received_file_client_N.txt` where N is the client ID

## Configuration

You can modify these variables in both `server.py` and `client.py`:

```python
HOST = '127.0.0.1'  # Server address
PORT = 9999          # Server port
MAX_CONNECTIONS = 100 # Number of connections to wait for
FILE_TO_SHARE = 'sample_file.txt'  # File to share
```

## Testing with Different Numbers

To test with a different number of clients (e.g., 10 for quick testing):

1. Edit `server.py` and change `MAX_CONNECTIONS = 10`
2. Run: `./launch_clients.sh 10`

## How It Works

1. **Server Initialization**: Server creates a socket and binds to the specified host:port
2. **Connection Phase**: Server accepts incoming connections one by one until reaching MAX_CONNECTIONS
3. **Parallel Transfer**: Once all connections are established, server creates a thread for each client
4. **File Transmission**: Each thread independently sends the file to its assigned client
5. **Completion**: All threads complete, connections close, server shuts down

## Architecture

```
Server                          Clients (x100)
  |                                  |
  |<------- Connect (1) -------------|
  |<------- Connect (2) -------------|
  |         ...                      |
  |<------- Connect (100) -----------|
  |                                  |
  |======= Send File (parallel) ===>|
  |======= Send File (parallel) ===>|
  |======= Send File (parallel) ===>|
  |         ...                      |
  |                                  |
```

## Performance Notes

- The parallel approach significantly reduces total transfer time compared to sequential
- Each client receives the file independently
- Network bandwidth is shared among all active transfers
- For very large files or many clients, consider implementing chunked transfers with progress reporting

## Cleanup

To remove received files:
```bash
rm received_file_client_*.txt
```

## Troubleshooting

**"Connection refused"**: Make sure the server is running before launching clients

**"Address already in use"**: Another process is using port 9999. Either stop that process or change the PORT variable

**Clients hanging**: Ensure you launch exactly MAX_CONNECTIONS clients. If fewer are launched, the server will wait indefinitely.
