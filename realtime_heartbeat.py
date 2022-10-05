# import numpy as np
# import serial
# import time
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
#
#
# fig, ax = plt.subplots()
# xdata, ydata = [], []
# ln, = plt.plot([], [], 'ro')
#
# def init():
#     ax.set_xlim(0, 1250)
#     ax.set_ylim(-2000, 5000)
#     return ln,
#
# def update(frame):
#     print(frame)
#     xdata.append(frame)
#     ydata.append(np.sin(frame))
#     ln.set_data(xdata, ydata)
#     return ln,
#
#
# baud_rate = 115200
# port = 'COM3'
#
#
# def read_com(com_port, baudrate, heartbeats):
#     print('Reading...')
#     serial_port = serial.Serial(port=com_port, baudrate=baudrate, timeout=1)
#     if serial_port.is_open:
#         size = serial_port.inWaiting()
#         if size:
#             data = serial_port.read(size)
#             res = data.decode("utf-8")
#             if len(res) == 8:
#                 # print("len == 8")
#                 # print(res)
#                 heartbeats.append(int(res))
#                 del heartbeats[0]
#                 print(heartbeats)
#                 return heartbeats
# # while True:
# #     try:
# #         z1serial = serial.Serial(port=port, baudrate=baud_rate, timeout=1)
# #         if z1serial.is_open:
# #             # start = time.time()
# #             while True:
# #                 size = z1serial.inWaiting()
# #                 # print(z1serial)
# #                 if size:
# #                     data = z1serial.read(size)
# #                     res = data.decode("utf-8")
# #                     if len(res) == 8:
# #                         # print("len == 8")
# #                         # print(res)
# #                         heartbeats.append(int(res))
# #                         del heartbeats[0]
# #                         print(heartbeats)
# #                         ani = FuncAnimation(fig, update, frames=heartbeats, init_func=init, blit=True)
# #                         plt.show()
# #                         # end = time.time()
# #                         # print(end - start)
# #                         # start = time.time()
# #                     # else:
# #                     #     print("len >= 8")
# #                     #     print(res)
# #                     #     print("--------")
# #                 # else:
# #                 #     print("Data not reading")
# #         else:
# #             z1serial.close()
# #             print('z1serial not open or Already in use')
# #     except serial.SerialException:
# #         print('COM4 not open')
# #         time.sleep(1)
#
#
# heartbeats = np.zeros(1250).astype(int).tolist()
# ani = FuncAnimation(fig, update, frames=read_com(port, baud_rate, heartbeats), init_func=init, blit=True)
# plt.show()
