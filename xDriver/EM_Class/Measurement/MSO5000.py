# xDrviver/EM_Class/Excitation/MSO5000.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# xDrvSetting begin
# device-type Measurement
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
sys.path.append('./xDriver/EM_Class/')
from typedef import *

def voltageScaleLimiter(voltagescale,channel_atte,freq):
    if(voltagescale>10):
        return 10*channel_atte
    if(voltagescale<1e-3 and freq < 20e6):
        return 1e-3*channel_atte
    if(voltagescale<2e-3 and freq > 20e6):
        return 2e-3*channel_atte
    return voltagescale

class MSO5000:
    def __init__(self,tunnel = "socket", address = ""):
        self.tunnel = tunnel.lower()
        self.address = address
        self.instr = None
        self.synctriggerEnable = False
        self.average_times = 1
        self._setup_port()
    
    def autoscale(self):
        self.instr.write(":AUT")

    def dutyCycle(self,channel:channel_number):
        cmd = ":MEAS:ITEM? PDUT"+","+channel.value
        return float(self.instr.ask(cmd))
    
    def getvoltage(self,channel:channel_number,items:wave_parameter):
        cmd = ":MEAS:ITEM? "+items.value+","+channel.value
        return float(self.instr.ask(cmd))
    
    def setSynctrigger(self,enable:bool):
        if enable:
            self.synctriggerEnable = True
        else:
            self.synctriggerEnable = False

    def getSampleDelay(self,freq):
        if(self.synctriggerEnable == False):
            sample_delay=0.1 if 0.1>4*1/freq*2**self.average_times else 4*1/freq*2**self.average_times
        else:
            sample_delay=1 if 0.1>6*4*1/freq*2**self.average_times else 6*4*1/freq*2**self.average_times
        return sample_delay

    def voltage(self,channel:channel_number,items:wave_parameter):
        max_try_times = 5
        loopcounter = 0
        voltage=self.getvoltage(channel,items)
        freq = self.freq(channel)
        channel_atte=self.getChannelAtte(channel)
        channel_scale=self.getChannelScale(channel)
        sample_delay=self.getSampleDelay(freq)
        # Auto scale for input channel when voltage is too large or too small
        while(voltage>channel_scale*8 and loopcounter<max_try_times):#When amplitude is too large, auto scale
            print("CH1 voltage scale too large, voltage is "+str(voltage)+",scale is "+str(channel_scale)+", Freq is "+str(freq))
            self.setChannelScale(channel,channel_scale*8)
            time.sleep(self.getSampleDelay(freq))
            channel_scale=channel_scale*8
            channel_scale = voltageScaleLimiter(channel_scale,channel_atte,freq)
            voltage=self.getvoltage(channel,wave_parameter.Peak2Peak)
            loopcounter=loopcounter+1
        loopCounter = 0
        # 当幅度过大的时候采用RMS代替Peak值
        while((voltage<2*channel_atte or voltage>6*channel_atte) and loopCounter<max_try_times):
            time.sleep(sample_delay)
            voltage=self.getvoltage(channel,wave_parameter.Peak2Peak)
            if(voltage>1e10):
                voltage=self.getvoltage(channel,wave_parameter.rms)*4*1.414
            channel_scale = voltageScaleLimiter(voltage/4,channel_atte,freq)
            self.setChannelScale(channel,channel_scale)#AutoScale when signal is too small
            loopCounter = loopCounter+1
        
        # if loopcounter==max_try_times:
        #     self.autoscale()
        #     self.setOSCChannel(inputChannel,outputChannel,self.syncChannel,self.sample_method,self.average_times,freq)
        #     print(channel1_scale)
        #     channel1_scale=self.getChannelScale(inputChannel)
        #     print(channel1_scale)
        # used to be used in PyBode, for some reason, now deprecated
        return voltage


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
        self.average_times=averagetimes
    
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
    mso = MSO5000(tunnel="visa", address="TCPIP::192.168.1.120::INSTR")
    # mso = MSO5000(tunnel="socket", address="192.168.1.120:5555")
    mso.autoscale()
