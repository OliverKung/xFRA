# xDrviver/EM_Class/Excitation/MSO5000.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# xDrvSetting begin
# device-type Excitation
# model MSO5000
# tunnel visa socket serial
# min-freq 0
# max-freq 25000000
# channel 2
# max-amp 5
# min-amp 0.001
# amp-unit VPP
# square yes
# square-max-freq 15000000
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

class MSO5000:
    def __init__(self,tunnel = "socket", address = ""):
        self.tunnel = tunnel.lower()
        self.address = address
        self.instr = None
        self._setup_port()

    def _setup_port(self):
        if self.tunnel == "socket":
            print("MSO5000: 使用 Socket 方式连接，地址：", self.address)
            # Socket 参考addr为192.168.1.1:5025，自动识别并建立通信端口
            sock_addr = self.address.split(":")
            ip = sock_addr[0]
            port = 5025
            if len(sock_addr) == 2:
                port = int(sock_addr[1])
            print(f"MSO5000: 连接到 IP={ip}, PORT={port}")
            self.instr = instru_socket.instru_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.instr.connect((ip, port))
        elif self.tunnel == "visa":
            print("MSO5000: 使用 visa 方式连接，地址：", self.address)
            rm = pyvisa.ResourceManager()
            self.instr = rm.open_resource(self.address)
        elif self.tunnel == "serial":
            print("MSO5000: 使用 serial 方式连接，地址：", self.address)
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
            print(f"MSO5000: 连接到 PORT={port}, BAUDRATE={baudrate}, BYTESIZE={bytesize}, PARITY={parity}, STOPBITS={stopbits}")
            self.instr = instru_serial.instru_serial(port=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=1)
        else:
            raise ValueError("MSO5000: 不支持的通信方式: " + self.tunnel)
        print("MSO5000: 连接成功")
        idn = self.instr.query("*IDN?")
        self.company = idn.split(",")[0]
        self.model = idn.split(",")[1]
        self.sn = idn.split(",")[2]
        self.firmware = idn.split(",")[3]
        print("MSO5000 IDN:", idn)
        self.instr.write("SYST:BEEP ON")
        self.instr.write("SYST:BEEP OFF")
    
    def set_freq_amp(self,freq,amplitude,channel:channel_number,unit:waveform_unit = waveform_unit.Vpp):
        if unit == waveform_unit.Vpp:
            amplitude_process = amplitude * 2
        elif unit == waveform_unit.Vrms:
            amplitude_process = amplitude * 2 * (2**0.5)
        elif unit == waveform_unit.dBm:
            amplitude_process = (10**(amplitude/20))*0.6324555320336759*2*2
        else:
            raise ValueError("MSO5000: 不支持的幅度单位: " + unit)
        if(channel == channel_number.ch1):
            channel_Str=":SOUR1"
        else:
            channel_Str=":SOUR2"
        self.instr.write(channel_Str+":VOLT "+str(amplitude_process))
        self.instr.write(channel_Str+":FREQ "+str(freq))

    def set_waveform_type(self,channel:channel_number,waveform:waveform_type):
        if(channel == channel_number.ch1):
            channel_Str=":SOUR1"
        else:
            channel_Str=":SOUR2"
        if(waveform == waveform_type.pulse):
            waveform_Str="PULS"
        elif(waveform == waveform_type.square):
            waveform_Str="SQU"
        elif(waveform == waveform_type.ramp):
            waveform_Str="RAMP"
        elif(waveform == waveform_type.sin):
            waveform_Str="SIN"
        self.instr.write(channel_Str+":APPL:"+waveform_Str)

    def setChannelOutputState(self,channel:channel_number,state):
        if(channel == channel_number.ch1):
            channel_Str=":SOUR1"
        else:
            channel_Str=":SOUR2"
        self.instr.write(channel_Str+":OUTP "+str(state))

    def setChannelLoadImpedance(self,channel:channel_number,loadimpedance):
        if(channel == channel_number.ch1):
            channel_Str=":SOUR1"
        else:
            channel_Str=":SOUR2"
        self.instr.write(channel_Str+":OUTP:IMP "+loadimpedance)
    
    def getMaxSquareFreq(self):
        return 15000000

if __name__=="__main__":
    # my_dsg=MSO5000(tunnel="visa",address="TCPIP::192.168.1.117::INSTR")
    my_dsg=MSO5000(tunnel="socket",address="192.168.1.117")
    # print(my_dsg.instr.ask("C2:BSWV?"))
    # my_dsg.set_sine_waveform(1e8,1,2)
