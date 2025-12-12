# xDrviver/EM_Class/Excitation/MSO5000.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# xDrvSetting begin
# device-type OSC
# model MSO5000
# tunnel visa socket serial
# average yes
# min-freq 0
# max-freq 350000000
# channel 4
# channelAttn 0.0001 0.0002 0.0005 0.001 0.002 0.005 0.01 0.02 0.05 0.1 0.2 0.5 1 2 5 10 20 50 100 200 500 1000 2000 5000 10000 20000 50000
# channelCoupling DC AC GND
# channelBandwidth Full 200000000 100000000 20000000
# samplemode norm peak aver hires
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

class channel_number(Enum):
    channel1="channel1"
    channel2="channel2"
    channel3="channel3"
    channel4="channel4"

class wave_parameter(Enum):
    vmax = "vmax"
    vmin = "vmin"
    vpp = "vpp"
    vrms = "vrms"
    ac_rms = "ac_rms"
    rise_rise_phase = "rise_rise_phase"
    rise_fall_phase = "rise_fall_phase"
    fall_rise_phase = "fall_rise_phase"
    fall_fall_phase = "fall_fall_phase"
    freq = "freq"

class sample_type(Enum):
    norm = "norm"
    peak = "peak"
    aver = "aver"
    hires = "hires"

class memory_store_method(Enum):
    screen_only=0
    RAW_data=1

class memory_store_depth(Enum):
    depth_1k="1k"
    depth_10k="10k"
    depth_100k="100k"
    depth_1M="1M"
    depth_10M="10M"
    depth_25M="25M"
    depth_50M="50M"
    depth_100M="100M"
    depth_200M="200M"
    depth_AUTO="AUTO"

class sample_method(Enum):
    normal="NORM"
    average="AVER"
    peak_detect="PEAK"
    high_resolution="HRES"

class couple_type(Enum):
    ac = "AC"
    dc = "DC"
    gnd = "GND"

class MSO5000:
    def __init__(self,tunnel = "socket", address = ""):
        self.tunnel = tunnel.lower()
        self.address = address
        self.instr = None
        self._setup_port()
    
    def autoscale(self):
        self.instr.write(":AUT")

    def dutyCycle(self,channel:channel_number):
        cmd = ":MEAS:ITEM? PDUT"+","+channel.value
        return float(self.instr.ask(cmd))
    
    def voltage(self,channel:channel_number,items:wave_parameter):
        cmd = ":MEAS:ITEM? "+items.value+","+channel.value
        return float(self.instr.ask(cmd))

    def freq(self,channel:channel_number):
        cmd = ":MEAS:ITEM? FREQ,"+channel.value
        return float(self.instr.ask(cmd))

    def phase(self,channelA:channel_number,channelB:channel_number):
        cmd = ":MEAS:ITEM? RRPH,"+channelA.value+","+channelB.value
        return float(self.instr.ask(cmd))

    def saveChanneltoFile(self,\
        file_name:str,channel:channel_number,\
        data_mode:memory_store_method=memory_store_method.screen_only,\
        memory_length:int=1000):
        with open(file_name,"w") as f:
            print("Store "+str(channel)+" "+str(memory_length)+" points data to "+file_name)
            if(data_mode==memory_store_method.screen_only):
                self.instr.write(":WAV:MODE NORM")
                self.instr.write(":WAV:POIN "+str(memory_length))
                self.instr.write(":WAV:FORMAT ASCII")
                data_line=self.instr.ask(":WAV:DATA?")
                data_point=data_line.split(",")
                f.write("Voltage\r\n")
                data_point[0]=data_point[0][11:]
                for data in data_point:
                    f.write(data+"\r\n")
            if(data_mode==memory_store_method.RAW_data):
                self.instr.write(":WAV:MODE RAW")
                self.instr.write(":WAV:POIN "+str(memory_length))
                self.instr.write(":WAV:FORMAT ASCII")
                self.instr.write(":STOP")
                print("start time:")
                print(time.time())
                data_line=self.instr.ask(":WAV:DATA?")
                print(time.time())
                print(data_line)
                data_point=data_line.split(",")
                f.write("Voltage\r\n")
                data_point[0]=data_point[0][11:]# remove head meaning less bytes
                for data in data_point:
                    f.write(data+"\r\n")
                self.instr.write(":RUN")
            print(channel.value+" Data of "+self.model+" locates at "+self.addr+" saved to "+file_name)

    def setAcquire(self,memdepth:memory_store_depth=memory_store_depth.depth_AUTO,\
        samplemode:sample_method=sample_method.normal):
        self.instr.write(":ACQ:TYPE "+samplemode.value)
        self.instr.write(":ACQ:MDEP "+memdepth.value)
        # print("Memory Depth of "+self.model+" locates at "+self.addr+" set to "+self.instr.ask(":ACQ:MDEP?"))
        # print("Acquire Mode of "+self.model+" locates at "+self.addr+" set to "+self.instr.ask(":ACQ:TYPE?"))
        time.sleep(1)

    def getScreenshoot(self,file_name:str):
        with open(file_name,"wb") as image:
            self.instr.write(":DISPlay:DATA?")
            img=self.instr.read_raw()
            image.write(img[11:])# remove head 11 meaning less bytes
            image.close()

    def setTimebaseScale(self,timebase_scale):
        self.instr.write(":TIM:SCAL "+str(timebase_scale))
    
    def setChannelOffet(self,channel:channel_number,offset):
        self.instr.write(":"+channel.value+":OFFS "+str(offset))

    def getChannelScale(self,channel:channel_number):
        return float(self.instr.ask(":"+channel.value+":SCAL?"))
    
    def setChannelScale(self,channel:channel_number,scale):
        self.instr.write(":"+channel.value+":SCAL "+str(scale))
    
    def getTimebaseScale(self):
        return float(self.instr.ask(":TIM:SCAL?"))
    
    def setChannelCouple(self,channel:channel_number,couple:couple_type):
        self.instr.write(":"+channel.value+":COUP "+couple.value)
    
    def setTriggerChannel(self,channel:channel_number):
        self.instr.write(":TRIG:EDGE:SOUR "+channel.value)
    
    def setTriggerLevel(self,voltage):
        self.instr.write(":TRIG:EDGE:LEV "+str(voltage))

    def setAverageTimes(self,averagetimes):
        self.instr.write(":ACQ:AVER "+str(2**averagetimes))
    
    def setChannelAtte(self,channel:channel_number,atte):
        self.instr.write(":"+channel.value+":PROB "+atte)
    
    def setChannelUnit(self,channel:channel_number,unit:str):
        self.instr.write(":"+channel.value+":UNIT "+unit)
    
    def getChannelAtte(self,channel:channel_number):
        Atte=self.instr.ask(":"+channel.value+":PROB?")
        return float(Atte)

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
    

if __name__ == "__main__":
    # 测试 MSO5000 类
    mso = MSO5000(tunnel="visa", address="TCPIP::192.168.1.121::INSTR")
    # mso = MSO5000(tunnel="socket", address="192.168.1.121:5555")
    mso.autoscale()
