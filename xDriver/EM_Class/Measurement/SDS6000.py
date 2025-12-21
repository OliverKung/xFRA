# xDrviver/EM_Class/Excitation/SDS6000.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# achieve around 2s/pts for 1kHz to 100kHz 100pt no average with visa connection and 1.5s/pts for socket connection
# xDrvSetting begin
# device-type Measurement
# model SDS6000
# tunnel visa socket serial
# average yes
# min-freq 0
# max-freq 2000000000
# channelNum 4
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

def typedef_translate(to_be_translage):
    if(type(to_be_translage) == wave_parameter):
        if to_be_translage == wave_parameter.Peak2Peak:
            return "PKPK"
        elif to_be_translage == wave_parameter.RMS:
            return "RMS"
        elif to_be_translage == wave_parameter.AVG:
            return "MEAN"
        elif to_be_translage == wave_parameter.FREQ:
            return "FREQ"
    elif(type(to_be_translage) == channel_number):
        if to_be_translage == channel_number.ch1:
            return "C1"
        elif to_be_translage == channel_number.ch2:
            return "C2"
        elif to_be_translage == channel_number.ch3:
            return "C3"
        elif to_be_translage == channel_number.ch4:
            return "C4"
    elif(type(to_be_translage) == sample_method):
        if to_be_translage == sample_method.normal:
            return "NORM"
        elif to_be_translage == sample_method.average:
            return "AVER"
        elif to_be_translage == sample_method.peak_detect:
            return "PEAK"
        elif to_be_translage == sample_method.high_resolution:
            return "ERES"
    pass

def voltageScaleLimiter(voltagescale,channel_atte,freq):
    if(voltagescale>10):
        return 10*channel_atte
    if(voltagescale<1e-3 and freq < 20e6):
        return 1e-3*channel_atte
    if(voltagescale<2e-3 and freq > 20e6):
        return 2e-3*channel_atte
    return voltagescale

class measure_item():
    def __init__(self,channel:channel_number,channelB:channel_number=None,items:wave_parameter=None,measure_idx=0):
        self.channel=channel
        self.items=items
        self.channelB=channelB

class SDS6000:
    def __init__(self,tunnel = "socket", address = ""):
        self.tunnel = tunnel.lower()
        self.address = address
        self.instr = None
        self.synctriggerEnable = False
        self.average_times = 1
        # list of measure_item，类型为 measure_item
        self.measure_items = []
        self._setup_port()
    
    # -------------------- xDrvEM 标准接口 --------------------
    # -------------------- 测量类标准接口 --------------------
    
    # 自动调节量程
    def autoscale(self):
        self.instr.write(":AUT")
        time.sleep(15)
    
    # 读取并自动调整电压量程
    def voltage(self,channel:channel_number,items:wave_parameter,freqIn=None):
        max_try_times = 10
        loopcounter = 0
        if freqIn is None:
            freq = self.freq(channel)
        else:
            freq = freqIn
        time.sleep(self.getSampleDelay(freq))
        print("Measuring voltage at freq %.2f Hz"%(freq))
        voltage=self.getvoltage(channel,wave_parameter.Peak2Peak)
        print("Initial voltage reading is %.4f V"%(voltage))
        self.setTimebaseScale(0.25*1/freq)
        print("Timebase scale set to %.6f s/div for freq %.2f Hz"%(0.25*1/freq,freq))
        channel_atte=self.getChannelAtte(channel)
        print("Channel attenuation is %.4f V/V"%(channel_atte))
        channel_scale=self.getChannelScale(channel)
        print("Initial channel scale is %.4f V/div"%(channel_scale))
        sample_delay=self.getSampleDelay(freq)
        print("Sample delay set to %.4f s for freq %.2f Hz with average times %d"%(sample_delay,freq,self.average_times))
        # print("Sample delay set to "+str(sample_delay)+" s for freq "+str(freq)+" Hz with average times "+str(self.average_times))
        # Auto scale for input channel when voltage is too large
        while(voltage>channel_scale*8 and loopcounter<max_try_times):#When amplitude is too large, auto scale
            # print("CH1 voltage scale too large, voltage is "+str(voltage)+",scale is "+str(channel_scale)+", Freq is "+str(freq))
            self.setChannelScale(channel,channel_scale*8)
            print("Auto adjusting voltage scale, voltage is "+str(voltage)+",scale is "+str(channel_scale*8)+", Freq is "+str(freq))
            time.sleep(self.getSampleDelay(freq))
            print("Measuring voltage at freq %.2f Hz"%(freq))
            channel_scale=channel_scale*8
            print("New channel scale is %.4f V/div"%(channel_scale))
            channel_scale = voltageScaleLimiter(channel_scale,channel_atte,freq)
            print("Limited channel scale is %.4f V/div"%(channel_scale))
            voltage=self.getvoltage(channel,wave_parameter.Peak2Peak)
            print("New voltage reading is %.4f V"%(voltage))
            loopcounter=loopcounter+1
            print("Auto adjusting voltage scale, voltage is "+str(voltage)+",scale is "+str(channel_scale)+", Freq is "+str(freq))
        # 当调整次数过多，重新进行一次自动调节
        if loopcounter==max_try_times:
            # print("voltage scale auto adjust failed, autoscale once. voltage is "+str(voltage)+",scale is "+str(channel_scale)+", Freq is "+str(freq))
            self.autoscale()
            print("voltage scale auto adjust failed, autoscale once. voltage is "+str(voltage)+",scale is "+str(channel_scale)+", Freq is "+str(freq))
            # autoscale之后，示波器通道设定可能改变，重新设置通道参数
            # self.setOSCChannel(inputChannel,outputChannel,self.syncChannel,self.sample_method,self.average_times,freq)
            channel_scale=self.getChannelScale(channel)
            print("After autoscale, new channel scale is %.4f V/div"%(channel_scale))
        # used to be used in PyBode, for some reason, now deprecated
        loopCounter = 0
        # 自动调整量程，直到读数在合理范围内
        while((voltage<2*channel_scale or voltage>6*channel_scale) and loopCounter<max_try_times):
            # print("Auto adjusting voltage scale, voltage is "+str(voltage)+",scale is "+str(channel_scale)+", Freq is "+str(freq))
            time.sleep(sample_delay)
            print("Measuring voltage at freq %.2f Hz"%(freq))
            voltage=self.getvoltage(channel,wave_parameter.Peak2Peak)
            print("Voltage reading is %.4f V"%(voltage))
            # 如果超量程读数出错，采用有效值重新计算
            if(voltage>1e10):
                voltage=self.getvoltage(channel,wave_parameter.rms)*4*1.414
                print("Overrange voltage reading error, using RMS value to recalculate, new voltage is %.4f V"%(voltage))
            channel_scale = voltageScaleLimiter(voltage/4,channel_atte,freq)
            print("Adjusted channel scale is %.4f V/div"%(channel_scale))
            self.setChannelScale(channel,channel_scale)
            print("Set channel scale to %.4f V/div"%(channel_scale))
            loopCounter = loopCounter+1
            print("Auto adjusting voltage scale, voltage is "+str(voltage)+",scale is "+str(channel_scale)+", Freq is "+str(freq))
        time.sleep(sample_delay)
        print("Final voltage measurement at freq %.2f Hz"%(freq))
        voltage=self.getvoltage(channel,items)
        print("Final voltage reading is %.4f V"%(voltage))
        return voltage

    # 读取频率
    def freq(self,channel:channel_number):
        index = 1
        for item in self.measure_items:
            if item.channel == channel and item.items == wave_parameter.FREQ:
                cmd = ":MEAS:ADV:P"+str(index)+":VAL?"
                return float(self.instr.query(cmd))
            index = index + 1
        # If not found, create a new measurement
        measure_idx = len(self.measure_items)+1
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+" ON")
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+":TYPE "+typedef_translate(wave_parameter.FREQ))
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+":SOUR1 "+typedef_translate(channel))
        self.measure_items.append(measure_item(channel=channel, items=wave_parameter.FREQ, measure_idx=measure_idx))
        time.sleep(0.1)
        cmd = ":MEAS:ADV:P"+str(measure_idx)+":VAL?"
        while True:
            try:
                float_value = float(self.instr.query(cmd))
                break
            except ValueError:
                time.sleep(0.1)
        return float_value

    # 读取相位差，范围-180~180度
    def phase(self,channelA:channel_number,channelB:channel_number):
        index = 1
        for item in self.measure_items:
            if item.channel ==  channelA and item.channelB == channelB:
                cmd = ":MEAS:ADV:P"+str(index)+":VAL?"
                return float(self.instr.query(cmd))
            index = index + 1
        # If not found, create a new measurement
        measure_idx = len(self.measure_items)+1
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+" ON")
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+":TYPE PHA")
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+":SOUR1 "+typedef_translate(channelA))
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+":SOUR2 "+typedef_translate(channelB))
        self.measure_items.append(measure_item(channel=channelA, channelB=channelB, items=wave_parameter.FREQ, measure_idx=measure_idx))
        time.sleep(0.1)
        cmd = ":MEAS:ADV:P"+str(measure_idx)+":VAL?"
        counter = 0
        while True:
            if(counter > 5):
                self.autoscale()
                time.sleep(3)
                self.voltage(channelA,wave_parameter.RMS)
                self.voltage(channelB,wave_parameter.RMS)
                time.sleep(0.1)
                counter = 0
            try:
                float_value = float(self.instr.query(cmd))
                break
            except ValueError:
                counter = counter+1
                time.sleep(0.1)
        return float_value

    # 设置采样模式
    def setSampleMode(self,samplemode:sample_method):
        if samplemode != sample_method.average:
            self.instr.write(":ACQ:TYPE "+typedef_translate(samplemode))
        else:
            pass

    # 设置耦合方式
    def setChannelCouple(self,channel:channel_number,couple:couple_type):
        self.instr.write(":"+channel.value+":COUP "+couple.value)

    # 设置通道偏移
    def setChannelOffet(self,channel:channel_number,offset):
        self.instr.write(":"+channel.value+":OFFS "+str(offset))

    # 设置通道衰减
    def setChannelAtte(self,channel:channel_number,atte):
        self.instr.write(":"+channel.value+":PROB VAL,"+atte)

    # 设置触发通道
    def setTriggerChannel(self,channel:channel_number):
        self.instr.write(":TRIG:EDGE:SOUR "+channel.value)

    # 设置平均次数
    def setAverageTimes(self,averagetimes):
        self.instr.write(":ACQ:TYPE AVER,"+str(2**averagetimes))
        self.average_times=averagetimes 
    
    # 设置通道单位
    def setChannelUnit(self,channel:channel_number,unit:str):
        self.instr.write(":"+channel.value+":UNIT "+unit)
    
    # 设置同步触发
    def setSynctrigger(self,enable:bool):
        if enable:
            self.synctriggerEnable = True
        else:
            self.synctriggerEnable = False

    # end----------------- 设置类接口 --------------------
    # -------------------- 回读类接口 --------------------

    # end----------------- 回读类接口 --------------------
    # end----------------- xDrvEM 标准接口 --------------------
    
    def getvoltage(self,channel:channel_number,items:wave_parameter):
        index = 1
        for item in self.measure_items:
            if item.channel == channel and item.items == items:
                cmd = ":MEAS:ADV:P"+str(index)+":VAL?"
                return float(self.instr.query(cmd))
            index = index + 1
        # If not found, create a new measurement
        measure_idx = len(self.measure_items)+1
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+" ON")
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+":TYPE "+typedef_translate(items))
        self.instr.write(":MEAS:ADV:P"+str(measure_idx)+":SOUR1 "+typedef_translate(channel))
        self.measure_items.append(measure_item(channel=channel, items=items, measure_idx=measure_idx))
        time.sleep(0.1)
        cmd = ":MEAS:ADV:P"+str(measure_idx)+":VAL?"
        while True:
            try:
                float_value = float(self.instr.query(cmd))
                break
            except ValueError:
                time.sleep(0.1)
        return float_value

    def getSampleDelay(self,freq):
        if(self.synctriggerEnable == False):
            sample_delay=0.1 if 0.1>4*1/freq*2**self.average_times else 4*1/freq*2**self.average_times
        else:
            sample_delay=1 if 0.1>6*4*1/freq*2**self.average_times else 6*4*1/freq*2**self.average_times
        return sample_delay

    def setTimebaseScale(self,timebase_scale):
        self.instr.write(":TIM:SCAL "+str(timebase_scale))
    
    def getChannelScale(self,channel:channel_number):
        return float(self.instr.query(":"+channel.value+":SCAL?"))
    
    def setChannelScale(self,channel:channel_number,scale):
        self.instr.write(":"+channel.value+":SCAL "+str(scale))
    
    def getTimebaseScale(self):
        return float(self.instr.query(":TIM:SCAL?"))

    def setTriggerLevel(self,voltage):
        self.instr.write(":TRIG:EDGE:LEV "+str(voltage))
    
    def getChannelAtte(self,channel:channel_number):
        Atte=self.instr.query(":"+channel.value+":PROB?")
        return float(Atte)

    def _setup_port(self):
        if self.tunnel == "socket":
            print("SDS6000: 使用 Socket 方式连接，地址：", self.address)
            # Socket 参考addr为192.168.1.1:5025，自动识别并建立通信端口
            sock_addr = self.address.split(":")
            ip = sock_addr[0]
            port = 5025
            if len(sock_addr) == 2:
                port = int(sock_addr[1])
            print(f"SDS6000: 连接到 IP={ip}, PORT={port}")
            self.instr = instru_socket.instru_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.instr.connect((ip, port))
        elif self.tunnel == "visa":
            print("SDS6000: 使用 visa 方式连接，地址：", self.address)
            rm = pyvisa.ResourceManager()
            self.instr = rm.open_resource(self.address)
        elif self.tunnel == "serial":
            print("SDS6000: 使用 serial 方式连接，地址：", self.address)
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
            print(f"SDS6000: 连接到 PORT={port}, BAUDRATE={baudrate}, BYTESIZE={bytesize}, PARITY={parity}, STOPBITS={stopbits}")
            self.instr = instru_serial.instru_serial(port=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=1)
        else:
            raise ValueError("SDS6000: 不支持的通信方式: " + self.tunnel)
        print("SDS6000: 连接成功")
        idn = self.instr.query("*IDN?")
        self.company = idn.split(",")[0]
        self.model = idn.split(",")[1]
        self.sn = idn.split(",")[2]
        self.firmware = idn.split(",")[3]
        print("SDS6000 IDN:", idn)
        self.instr.write("SYST:BEEP ON")
        self.instr.write("SYST:BEEP OFF")
        self.instr.write(":MEAS:ADV:CLE")  # 清除所有测量设置
    

if __name__ == "__main__":
    # 测试 SDS6000 类
    mso = SDS6000(tunnel="visa", address="TCPIP::192.168.1.119::INSTR")
    # mso = SDS6000(tunnel="socket", address="192.168.1.120:5555")
    # mso.autoscale()
    mso.instr.write(":MEAS:SIMP:ITEM PKPK,ON")
    mso.instr.write(":MEAS:SIMP:SOUR C1")
    print("CH1 Voltage Vpp:", mso.getvoltage(channel_number.ch1, wave_parameter.Peak2Peak))
    print("CH2 Voltage VRMS:", mso.getvoltage(channel_number.ch2, wave_parameter.AVG))
    print("CH1 Frequency:", mso.freq(channel_number.ch1))
    print("CH1-CH2 Phase:", mso.phase(channel_number.ch1, channel_number.ch2))
    # for i in range(1000):
    #     print("CH1 Voltage Vpp:", mso.getvoltage(channel_number.ch1, wave_parameter.Peak2Peak))
    #     print("CH2 Voltage VRMS:", mso.getvoltage(channel_number.ch2, wave_parameter.AVG))
    #     print("CH1 Frequency:", mso.freq(channel_number.ch1))
    #     time.sleep(0.1)