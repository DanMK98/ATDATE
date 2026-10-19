
import socket

with socket.socket() as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 6001))
    server.listen(1)

    connection, _ = server.accept()
    with connection:
        connection.sendall(b"\x01\x02")