from server import ServerHandler

server = ServerHandler()
server.connect()

print(f"[LISTENING] Server is listening on {server.SERVER_NAME}")
while True:
    server.client_accept()


