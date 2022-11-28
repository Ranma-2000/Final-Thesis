import serial.tools.list_ports
import serial


def get_available_port():
    print("Get start!")
    ports = serial.tools.list_ports.comports()
    connected_port = []
    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))
        connected_port.append(port)
    return connected_port[0]


def connect_serial_port(port, baud_rate=115200, timeout=1):
    serial_port = serial.Serial(port=port, baudrate=baud_rate, timeout=timeout)
    return serial_port


