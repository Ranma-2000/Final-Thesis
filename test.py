import serial.tools.list_ports
comlist = serial.tools.list_ports.comports()
connected = []
for element in comlist:
    connected.append(element.device)
print("Connected COM ports: " + str(connected))
baud_rate = 115200
port = connected[1]
z1serial = serial.Serial(port=port, baudrate=baud_rate, timeout=1)

if z1serial.is_open():
    size = z1serial.inWaiting()
    data = z1serial.read(size)
    res = data.decode("utf-8")
    print(res)