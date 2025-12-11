import custom_tunnel.instru_socket as instru_socket
import custom_tunnel.instru_serial as instru_serial

class MSO5000:
    def __init__(self,tunnel = "socket", address = ""):
        if tunnel == "socket":
            print("MSO5000: 使用 Socket 方式连接，地址：", address)
            # Socket 参考addr为192.168.1.1:5025，自动识别并建立通信端口
            sock_addr = address.split(":")
            ip = sock_addr[0]
            port = 5025
            if len(sock_addr) == 2:
                port = int(sock_addr[1])
            print(f"MSO5000: 连接到 IP={ip}, PORT={port}")
            self.tunnel = instru_socket.instru_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tunnel.connect((ip, port))
        elif tunnel == "VISA":
            print("MSO5000: 使用 VISA 方式连接，地址：", address)
        elif tunnel == "Serial":
            print("MSO5000: 使用 Serial 方式连接，地址：", address)
        elif tunnel == "VXI11":
            print("MSO5000: 使用 VXI11 方式连接，地址：", address)