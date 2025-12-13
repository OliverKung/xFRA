# xDrviver/EM_Class/Excitation/SDG2000X.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# xDrvSetting begin
# device-type Excitation
# model SDG2000X
# tunnel visa socket serial
# min-freq 0
# max-freq 120000000
# channel 2
# max-amp 10
# min-amp 0.001
# amp-unit VPP
# square yes
# square-max-freq 25000000
# xDrvSetting end
#python LibreVNA.py --device-address 192.168.1.100 --start-freq 1e6 --stop-freq 1e9 --sweep-type LIN --sweep-points 501 --ifbw 1e3 --source-level -10 --averages 3 --output-file meas.s2p

import sys
sys.path.append('./')
from custom_tunnel import instru_socket
from custom_tunnel import instru_serial
import socket,serial
import pyvisa
import time
from enum import Enum
sys.path.append('./xDriver/EM_Class/')
from typedef import *

class SDG2000X:
    def __init__(self,tunnel = "socket", address = ""):
        self.tunnel = tunnel.lower()
        self.address = address
        self.instr = None
        self._setup_port()

    def _setup_port(self):
        if self.tunnel == "socket":
            print("SDG2000X: 使用 Socket 方式连接，地址：", self.address)
            # Socket 参考addr为192.168.1.1:5025，自动识别并建立通信端口
            sock_addr = self.address.split(":")
            ip = sock_addr[0]
            port = 5025
            if len(sock_addr) == 2:
                port = int(sock_addr[1])
            print(f"SDG2000X: 连接到 IP={ip}, PORT={port}")
            self.instr = instru_socket.instru_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.instr.connect((ip, port))
        elif self.tunnel == "visa":
            print("SDG2000X: 使用 visa 方式连接，地址：", self.address)
            rm = pyvisa.ResourceManager()
            self.instr = rm.open_resource(self.address)
        elif self.tunnel == "serial":
            print("SDG2000X: 使用 serial 方式连接，地址：", self.address)
            # Socket 参考addr为192.168.1.1:115200,8,n,1，自动识别并建立通信端口
            serial_addr = self.address.split(":")
            port = serial_addr[0]
            baudrate = 115200
            if len(serial_addr) >= 2:
                baudrate = int(serial_addr[1])
            bytesize = 8
            parity = 'N'
            stopbits = 1
            if len(serial_addr) >= 5:
                bytesize = int(serial_addr[2])
                parity = serial.PARITY_NONE
                if serial_addr[3] == 'E':
                    parity = serial.PARITY_EVEN
                elif serial_addr[3] == 'O':
                    parity = serial.PARITY_ODD
                stopbits = int(serial_addr[4])
            print(f"SDG2000X: 连接到 PORT={port}, BAUDRATE={baudrate}, BYTESIZE={bytesize}, PARITY={parity}, STOPBITS={stopbits}")
            self.instr = instru_serial.instru_serial(port=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=1)
        else:
            raise ValueError("SDG2000X: 不支持的通信方式: " + self.tunnel)
        print("SDG2000X: 连接成功")
        idn = self.instr.query("*IDN?")
        self.company = idn.split(",")[0]
        self.model = idn.split(",")[1]
        self.sn = idn.split(",")[2]
        self.firmware = idn.split(",")[3]
        print("SDG2000X IDN:", idn)
        self.instr.write("SYST:BEEP ON")
        self.instr.write("SYST:BEEP OFF")
    
    def set_freq_amp(self,freq,amplitude,channel:channel_number):
        if(channel == channel_number.ch1):
            channel_Str="C1"
        else:
            channel_Str="C2"
        self.instr.write(channel_Str+":BSWV AMP,"+str(amplitude))
        self.instr.write(channel_Str+":BSWV FRQ,"+str(freq))

    def set_waveform_type(self,channel:channel_number,waveform:waveform_type):
        if(channel == channel_number.ch1):
            channel_Str="C1"
        else:
            channel_Str="C2"
        self.instr.write(channel_Str+":BSWV WVTP,"+waveform.value)

    def setChannelOutputState(self,channel:channel_number,state):
        if(channel == channel_number.ch1):
            channel_Str="C1"
        else:
            channel_Str="C2"
        self.instr.write(channel_Str+":OUTP "+"ON" if state==1 else "OFF")

    def setChannelLoadImpedance(self,channel:channel_number,loadimpedance):
        if(channel == channel_number.ch1):
            channel_Str="C1"
        else:
            channel_Str="C2"
        self.instr.write(channel_Str+":OUTP LOAD,"+loadimpedance)
    
    def getMaxSquareFreq(self):
        return 25000000

if __name__=="__main__":
    # my_dsg=SDG2000X(tunnel="visa",address="TCPIP::192.168.1.117::INSTR")
    my_dsg=SDG2000X(tunnel="socket",address="192.168.1.117")
    # print(my_dsg.instr.ask("C2:BSWV?"))
    # my_dsg.set_sine_waveform(1e8,1,2)
