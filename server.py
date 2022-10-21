import socket
import pickle
import codecs

def get_data(client_obj):
    trans_data = b""
    while True:
        socket_receiver = client_obj.recv(4096)
        if not socket_receiver:
            break
        trans_data += socket_receiver
        print(trans_data)
    return trans_data.decode('utf-8')


HOST = '127.0.0.1'
PORT = 8000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(2)

while True:
    client, addr = s.accept()

    try:
        print('Connected by', addr)
        while True:
            print("Got")
            data = client.recv(1650)
            encoding = 'utf-8'

            print(data.decode(encoding))
            # data = pickle.loads(data)
            if data == "quit":
                break
            """if not data:
                break
            """
            # print(data)

    finally:
        client.close()

s.close()
