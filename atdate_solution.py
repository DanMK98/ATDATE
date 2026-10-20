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

        date = time.strftime("%a %b %d %H:%M:%S %Z %Y", time.localtime(unix_time)).replace(" 0", " ", 1)
        print(date)

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
                data_client = receive_exactly(connection, 4)
                client_seconds = struct.unpack("!I", data_client)[0]
                server_seconds = int(time.time()) + TIME_EPOCH_OFFSET
                delta = client_seconds - server_seconds

                if delta < 0:
                    comparison = b"\x00"
                elif delta == 0:
                    comparison = b"\x01"
                else:
                    comparison = b"\x02"

                # Response: 1 comparison byte, 4 timestamp bytes, 8 delta bytes.
                data = comparison + struct.pack("!Iq", server_seconds, delta)
                connection.sendall(data)

                if debug:
                    print(f"Sent {len(data)} bytes to {address}")
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

def tcp_client(serverhost, port, debug):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((serverhost, port))
        sock.settimeout(None)

        if debug:
            print(f"Connected to TCP server at {serverhost}:{port}")

        while True:
            client_seconds = int(time.time()) + TIME_EPOCH_OFFSET
            sock.sendall(struct.pack("!I", client_seconds))

            # Read each part once, in the same order used by the server.
            comparison = receive_exactly(sock, 1)
            server_data = receive_exactly(sock, 4)
            delta_data = receive_exactly(sock, 8)

            server_seconds = struct.unpack("!I", server_data)[0]
            delta = struct.unpack("!q", delta_data)[0]

            if comparison == b"\x00":
                message = "Client clock is behind."
            elif comparison == b"\x01":
                message = "Clocks match."
            elif comparison == b"\x02":
                message = "Client clock is ahead."
            else:
                raise ValueError("Unknown comparison byte")

            if debug:
                print("Received 13 bytes from server")

            unix_time = server_seconds - TIME_EPOCH_OFFSET
            date = time.strftime("%a %b %d %H:%M:%S %Z %Y", time.localtime(unix_time)).replace(" 0", " ", 1)
            print(f"{date} | {message} Delta (client - server): {delta:+d} seconds.", flush=True)

            # Wait before capturing the next fresh client timestamp.
            time.sleep(1)

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

    args = parser.parse_args()

    if args.mode in ["cu", "ct"] and not args.serverhost:
        parser.error("Server hostname is required for client modes.")

    if 1 <= args.port <= 65535:
        pass
    else:
        parser.error("Invalid port. Please specify a port between 1 and 65535.")

    try:
        if args.mode == "cu":
            udp_client(args.serverhost, args.port, args.debug)
        elif args.mode == "ct":
            tcp_client(args.serverhost, args.port, args.debug)
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