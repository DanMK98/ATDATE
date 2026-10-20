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

                

                time_seconds = int(time.time()) + TIME_EPOCH_OFFSET
                data = struct.pack("!I", time_seconds)
                connection.sendall(data)

                value_c = receive_exactly(connection, 4)
                int_value_c = struct.unpack("!I", value_c)[0]
                #print(int_value_c)

                if debug:
                    print(f"Sent {len(data)} bytes to {address}")
                
                if int_value_c == 1:
                    if debug:
                        print(int_value_c)
                    time.sleep(1)
                    continue

                if int_value_c == 0:
                    if debug:
                        print(int_value_c)
                    print("Reached count limit. Closing connection.")
                    break
                
                if int_value_c != 0 | 1:
                   print("Exception: did not receive appropriate value.")
                   break

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

def tcp_client(serverhost, port, count, debug):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((serverhost, port))      

        # Wait for updates without a timeout after connecting
        sock.settimeout(None)

        if debug:
            print(f"Connected to TCP server at {serverhost}:{port}")

        received_count = count


        while True:
            data = receive_exactly(sock, 4)

            if debug:
                print(f"Received {len(data)} bytes from server")

            time_Seconds = struct.unpack("!I", data)[0]
            unix_time = time_Seconds - TIME_EPOCH_OFFSET

            date = time.strftime("%a %b %d %H:%M:%S %Z %Y", time.localtime(unix_time)).replace(" 0", " ", 1)
            
            received_count += -1

            if received_count > 0:
                value_1 = struct.pack("!I", 1)
                if debug:
                    print(value_1)
                sock.sendall(value_1)
                print(date)

            elif received_count == 0:
                value_0 = struct.pack("!I", 0)
                if debug:
                    print(value_0)
                sock.sendall(value_0)
                print(date)
                print("Reached count limit. Closing connection.")
                break

            elif received_count == -1:
                value_0 = struct.pack("!I", 0)
                sock.sendall(value_0)
                print("Closing connection.")
                break

            elif received_count < -1:
                print("Count parameter must be greater or equal to 0. Closing connection.")
                break

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
        "-c",
        dest="count",
        type=int,
        default=1,
        help="Specifies the number of times"
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
            tcp_client(args.serverhost, args.port, args.count, args.debug)
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