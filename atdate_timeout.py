import argparse
import socket
import struct
import time
import threading

TIME_EPOCH_OFFSET = 2208988800  # Time difference between 1900 and 1970 in seconds

def udp_client(serverhost, port, debug):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(5)

        sock.connect((serverhost, port))

        if debug:
            print(f"Sending empty UDP datagram to {serverhost}:{port}")

        sock.send(b"")

        data = sock.recv(1024)

        if debug:
            print(f"Received {len(data)} bytes from server")

        if len(data) != 4:
            raise ValueError("TIME response must exactly be 4 bytes long")

        time_Seconds = struct.unpack("!I", data)[0]
        unix_time = time_Seconds - TIME_EPOCH_OFFSET

        date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_time))
        print(f"Current time: {date}")

def receive_exactly(sock, size):
    data = b""

    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before receiving expected data")
        data += chunk
    return data

def handle_client(connection, address, debug):
    with connection:
        if debug:
            print(f"Accepted connection from {address}")

        try:
            while True:
                time_seconds = int(time.time()) + TIME_EPOCH_OFFSET
                data = struct.pack("!I", time_seconds)
                connection.sendall(data)

                if debug:
                    print(f"Sent {len(data)} bytes to {address}")

                time.sleep(1)  # Send updates every second
        except (ConnectionError, OSError) as e:
            if debug:
                print(f"Connection with {address} closed: {e}")

def tcp_server(port, debug):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.bind(("0.0.0.0", port))
        server.listen()

        print(f"TIME server running on port {port}")

        while True:
            connection, address = server.accept()

            thread = threading.Thread(target=handle_client, args=(connection, address, debug), daemon=True)
            thread.start()

def tcp_client(serverhost, port, timeout, debug):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        sock.settimeout(1)
        sock.connect((serverhost, port))
        sock.settimeout(timeout)  # Set the timeout for subsequent operations      

        if debug:
            print(f"Connected to TCP server at {serverhost}:{port}")

        while True:
            data = receive_exactly(sock, 4)

            if debug:
                print(f"Received {len(data)} bytes from server")

            time_Seconds = struct.unpack("!I", data)[0]
            unix_time = time_Seconds - TIME_EPOCH_OFFSET

            date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_time))
            print(f"Current time: {date}")




def main():
    parser = argparse.ArgumentParser(
        description="TIME protocol client and server"
    )

    parser.add_argument(
        "-s",
        dest="serverhost",
        type=str,
        default="localhost",
        help="Server hostname or IP address to connect to (default: localhost)",
    )

    parser.add_argument(
        "-p",
        dest="port",
        type=int,
        default=37,
        help="Port to connect to (default: 37)",
    )

    parser.add_argument(
        "-m",
        dest="mode",
        choices=["cu", "ct", "s"],
        default="cu",
        help="Mode of operation: 'cu' for client using UDP, 'ct' for client using TCP, 's' for server (default: cu)",
    )

    parser.add_argument(
        "-d",
        dest="debug",
        action="store_true",
        help="Enable debug output",
    )

    parser.add_argument(
        "-t",
        dest="timeout",
        type=int,
        default=5,
        help="Timeout for socket operations in seconds (TCP only)",
    )

    args = parser.parse_args()

    if args.mode in ["cu", "ct"] and not args.serverhost:
        parser.error("Server hostname is required for client modes.")

    if 1 <= args.port <= 65535:
        pass
    else:
        parser.error("Invalid port. Please specify a port between 1 and 65535.")

    if args.timeout < 1:
        parser.error("Timeout must be a positive integer for TCP client mode.")

    try:
        if args.mode == "cu":
            udp_client(args.serverhost, args.port, args.debug)
        elif args.mode == "ct":
            tcp_client(args.serverhost, args.port, args.timeout, args.debug)
        else:
            tcp_server(args.port, args.debug)

    except KeyboardInterrupt:
        print("SIGINT received. Closing program.")
    except socket.timeout:
        print("Error: Connection timed out.")
    except (OSError, ValueError) as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()
