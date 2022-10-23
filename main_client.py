import numpy as np
from client import ClientHandler

heartbeats = list(np.zeros(1250).astype(str))
client_obj = ClientHandler()
client_obj.connect_server()
while True:
    client_obj.run(heartbeats)
