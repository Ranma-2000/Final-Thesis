from server import ServerHandler

server = ServerHandler()
server.connect()

print(f"[LISTENING] Server is listening on {server.SERVER_NAME}")
server.client_accept()



