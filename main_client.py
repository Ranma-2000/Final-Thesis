import numpy as np
from client import ClientHandler
import logging

heartbeats = list(np.zeros(1250).astype(str))
client_obj = ClientHandler()
client_obj.connect_server()
while True:
    try:
        client_obj.run(heartbeats)
    except KeyboardInterrupt:
        break
    except BaseException:
        logging.exception("An exception was thrown!")
        break