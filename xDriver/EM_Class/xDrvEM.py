#!/usr/bin/env python3
import argparse
import importlib
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import math
from tqdm import tqdm
import argparse
from enum import Enum
import time

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

# -------------------- 参数解析函数 --------------------
def parse_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--m-device-model", type=str, required=True,
                        help="测量设备型号，对应 Measurement/<型号>.py 中的类名")
    parser.add_argument("--e-device-model", type=str, required=True,
                        help="激励设备型号，对应 Excitation/<型号>.py 中的类名")
    parser.add_argument("--m-device-tunnel", type=str, default="socket",
                        help="测量设备通信隧道类型，socket, visa 或 serial")
    parser.add_argument("--e-device-tunnel", type=str, default="socket",
                        help="激励设备通信隧道类型，socket, visa 或 serial")
    parser.add_argument("--m-device-addr", type=str, default="",
                        help="测量设备通信地址，格式取决于隧道类型"
                             "(socket: ip:port, visa: resource string, serial: port:baudrate:bits:parity:stopbits)")
    parser.add_argument("--e-device-addr", type=str, default="",
                        help="激励设备通信地址，格式取决于隧道类型"
                             "(socket: ip:port, visa: resource string, serial: port:baudrate:bits:parity:stopbits)")
    parser.add_argument("--average-sample-times",type=int,default=4,help="the average times of average sample, input the power of average times, for example, default value is 4, this means 2^4=16 times average")
    parser.add_argument("--average", type=int, default=1, help="测量平均次数")
    parser.add_argument("--start-freq", type=float, default=1e3, help="Sweep start frequency in Hz")
    parser.add_argument("--end-freq", type=float, default=1e6, help="Sweep stop frequency in Hz")
    parser.add_argument('--sweep-type', type=str, default='LOG', help='Sweep type (LIN or LOG)')
    parser.add_argument('--sweep-points', type=int, default=201, help='Number of sweep points')
    parser.add_argument('--ifbw', type=float, default=1000.0, help='IF bandwidth in Hz')
    parser.add_argument('--variable-amp', action='store_true', help='Enable variable source amplitude')
    parser.add_argument('--source-level', type=float, default=-10.0, help='Source level in dBm')
    parser.add_argument('--calibration', type=str, help='Path to calibration file')
    parser.add_argument('--output-file', type=str, required=True, help='Path to output data file')
    parser.add_argument('--sample-method', type=str,default="normal",help="Sample Method: Normal,Peak,Average and Hi-Res")
    parser.add_argument('--excition-channel', type=str,default="channel1",help="the excition channel of function generator,default is \"channel1\"")
    parser.add_argument('--input-channel', type=str,default="channel1",help="network input channel of osc,default is \"channel1\"")
    parser.add_argument('--output-channel', type=str,default="channel2",help="network output channel of osc,default is \"channel2\"")
    parser.add_argument('--sync-trigger', type=str,default="channel2",help="the sync trigger function generator sync number, default is \"channel2\"")
    parser.add_argument('--sync-channel', type=str,default="channel3",help="the sync trigger channel number, default is \"channel3\"")
    parser.add_argument('--sync-trigger-enable', type=str,default="false",help="sync Trigger function enable, default is flase")

    return parser.parse_args()

# -------------------- 辅助函数 --------------------
def voltageScaleLimiter(voltagescale,channel_atte,freq):
    if(voltagescale>10):
        return 10*channel_atte
    if(voltagescale<1e-3 and freq < 20e6):
        return 1e-3*channel_atte
    if(voltagescale<2e-3 and freq > 20e6):
        return 2e-3*channel_atte
    return voltagescale

# -------------------- 动态加载函数 --------------------
def load_device_class(sub_dir: str, model: str):
    """
    从 sub_dir/<model>.py 中导入同名的类并返回
    sub_dir 必须是 'Measurement' 或 'Excitation'
    """
    base_path = Path(__file__).resolve().parent
    module_path = base_path / sub_dir / f"{model}.py"

    if not module_path.exists():
        print(f"[Error] 文件不存在: {module_path}")
        sys.exit(1)

    # 构造模块名：Measurement.MSO5000  或  Excitation.SDG2000
    module_name = f"{sub_dir}.{model}"

    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        print(f"[Error] 导入模块失败: {e}")
        sys.exit(1)

    # 获取类对象
    cls = getattr(mod, model, None)
    if cls is None:
        print(f"[Error] 在 {module_name}.py 中找不到类定义: {model}")
        sys.exit(1)

    return cls

# -------------------- 主测量对象定义 --------------------

class PyBode():
    def __init__(self,e_model,m_model,e_addr,m_addr,e_tunnel,m_tunnel):
        Meas = load_device_class("Measurement", m_model)
        Exct = load_device_class("Excitation", e_model)
        self.m_instru=Meas(tunnel = m_tunnel, address = m_addr)
        self.e_instru=Exct(tunnel = e_tunnel, address = e_addr)
        self.syncTriggerEnable = False
        self.average_times = 4

    def run(self,startFreq,stopFreq,totalPoints,Ampilitude,\
            ExcitationChannel:channel_number,\
            inputChannel:channel_number,\
            outputChannel:channel_number,\
            syncTrigger:channel_number,\
            ):
        my_osc=self.m_instru
        my_dsg=self.e_instru
        max_try_times=5
        freq_list=np.logspace(math.log(startFreq,10),math.log(stopFreq,10),int(totalPoints),endpoint = True)
        df=pd.DataFrame({}, columns=['freq', 'gain', 'phase'])
        # print(freq_list)
        timebase_scale=10
        my_osc.setTimebaseScale(10)

        channel1_scale=my_osc.getChannelScale(inputChannel)
        channel2_scale=my_osc.getChannelScale(outputChannel)
        counter = 1

        channel1_atte = my_osc.getChannelAtte(inputChannel)
        channel2_atte = my_osc.getChannelAtte(outputChannel)
        filename='bode_data_'+time.strftime("%Y-%m-%d-%H%M%S", time.localtime(time.time()))+".csv"
        with open(".\\temp\\datafilename.txt","w") as f:
            f.write(filename)
        with open(".\\ExampleData\\"+filename,"w") as f:
            for freq in tqdm(freq_list):
                with open(".\\temp\\progress.csv","w") as tmp:
                    tmp.write(str(freq)+","+str(counter)+","+str(int(totalPoints)))
                    tmp.close()
                    counter=counter+1
                if(self.syncTriggerEnable == False):
                    sample_delay=0.1 if 0.1>4*1/freq*2**self.average_times else 4*1/freq*2**self.average_times
                else:
                    sample_delay=1 if 0.1>6*4*1/freq*2**self.average_times else 6*4*1/freq*2**self.average_times
                # print(sample_delay)
                my_dsg.set_freq_amp(freq,Ampilitude,ExcitationChannel)

                if(self.syncTriggerEnable == True):
                    freqSquare=freq
                    while(freqSquare>25e6):
                        freqSquare=freqSquare/2
                    my_dsg.set_freq_amp(freqSquare,1,syncTrigger)    #set signal source
                # print(freq)
                my_osc.setTimebaseScale(0.25*1/freq)
                time.sleep(sample_delay) #wait for measure
                
                voltage1=my_osc.voltage(inputChannel,wave_parameter.Peak2Peak)
                voltage2=my_osc.voltage(outputChannel,wave_parameter.Peak2Peak)
                loopCounter = 0
                while(voltage1>channel1_scale*8 and loopCounter<max_try_times):#When amplitude is too large, auto scale
                    print("CH1 voltage scale too large, voltage is "+str(voltage1)+",scale is "+str(channel1_scale)+", Freq is "+str(freq))
                    my_osc.setChannelScale(inputChannel,channel1_scale*8)
                    time.sleep(sample_delay)
                    channel1_scale=channel1_scale*8
                    channel1_scale = voltageScaleLimiter(channel1_scale,channel1_atte,freq)
                    voltage1=my_osc.voltage(inputChannel,wave_parameter.Peak2Peak)
                    loopCounter=loopCounter+1
                
                if loopCounter==max_try_times:
                    my_osc.autoscale()
                    self.setOSCChannel(inputChannel,outputChannel,self.syncChannel,self.sample_method,self.average_times,freq)
                    print(channel1_scale)
                    channel1_scale=my_osc.getChannelScale(inputChannel)
                    print(channel1_scale)

                loopCounter = 0
                while(voltage2>channel2_scale*8 and loopCounter<max_try_times):#When amplitude is too large, auto scale
                    print("CH2 voltage scale too large, voltage is "+str(voltage2)+",scale is "+str(channel2_scale)+", Freq is "+str(freq))
                    my_osc.setChannelScale(outputChannel,channel2_scale*8)
                    time.sleep(sample_delay)
                    channel2_scale=channel2_scale*8
                    channel2_scale = voltageScaleLimiter(channel2_scale,channel2_atte,freq)
                    voltage2=my_osc.voltage(outputChannel,wave_parameter.Peak2Peak)
                    print(voltage2)
                    loopCounter=loopCounter+1
                
                if loopCounter==max_try_times:
                    my_osc.autoscale()
                    self.setOSCChannel(inputChannel,outputChannel,self.syncChannel,self.sample_method,self.average_times,freq)
                    print(channel2_scale)
                    channel2_scale=my_osc.getChannelScale(outputChannel)
                    print(channel2_scale)
                    time.sleep(5)

                loopCounter = 0
                while((voltage1<2*channel1_scale or voltage1>6*channel1_scale) and loopCounter<max_try_times):
                    time.sleep(sample_delay)
                    voltage1=my_osc.voltage(inputChannel,wave_parameter.Peak2Peak)
                    if(voltage1>1e10):
                        voltage1=my_osc.voltage(inputChannel,wave_parameter.rms)*4*1.414
                    channel1_scale = voltageScaleLimiter(voltage1/4,channel1_atte,freq)
                    my_osc.setChannelScale(inputChannel,channel1_scale)#AutoScale when signal is too small
                    loopCounter = loopCounter+1
                loopCounter = 0
                while((voltage2<2*channel2_scale or voltage2>6*channel2_scale) and loopCounter<max_try_times):
                    time.sleep(sample_delay)
                    voltage2=my_osc.voltage(outputChannel,wave_parameter.Peak2Peak)
                    if(voltage2>1e10):
                        voltage2=my_osc.voltage(inputChannel,wave_parameter.rms)*4*1.414
                    channel2_scale = voltageScaleLimiter(voltage2/4,channel2_atte,freq)
                    my_osc.setChannelScale(outputChannel,channel2_scale)
                    loopCounter = loopCounter+1

                time.sleep(sample_delay) #wait for measure

                voltage1=my_osc.voltage(inputChannel,wave_parameter.RMS)

                time.sleep(sample_delay)
                voltage2=my_osc.voltage(outputChannel,wave_parameter.RMS)
                print("freq:",freq)
                print("voltage1:",voltage1)
                print("voltage2:",voltage2)
                phase=-1*my_osc.phase(inputChannel,outputChannel)
                while(phase>360 or phase <-360):
                    phase=-1*my_osc.phase(inputChannel,outputChannel)
                loopCounter = 0
                while(phase > 180 or phase<-180 and loopCounter<max_try_times):
                    phase=-1*my_osc.phase(inputChannel,outputChannel)
                    loopCounter = loopCounter + 1
                if(loopCounter >= 20):
                    phase = 0
                gain=20*math.log(voltage2/voltage1,10)
                # print(str(freq)+","+str(voltage1)+","+str(voltage2)+","+str(gain)+","+str(phase))
                f.write(str(freq)+","+str(voltage1)+","+str(voltage2)+","+str(gain)+","+str(phase)+","+str(0.5*Ampilitude/math.sqrt(2))+"\r")
                df.loc[len(df.index)]=[freq,gain,phase]
            f.close()

    def setChannel(self,excitionchannel,inputchannel,outputchannel,\
                   synctrigger,syncchannel,samplemethod,averageTimes):
        self.sample_method=samplemethod
        self.average_times=averageTimes
        self.syncChannel=syncchannel
        if(self.syncTriggerEnable == True):
            self.osc.setChannelCouple(inputchannel,couple_type.ac)
            self.osc.setChannelCouple(outputchannel,couple_type.ac)
            self.osc.setChannelCouple(syncchannel,couple_type.ac)
            self.osc.setChannelOffet(inputchannel,0)
            self.osc.setChannelOffet(outputchannel,0)
            self.osc.setChannelOffet(syncchannel,0)
            self.osc.setAcquire(samplemode=samplemethod)
            self.osc.setAverageTimes(averageTimes)
            self.osc.setTriggerChannel(syncchannel)
            self.osc.setTriggerLevel(0)

            self.afg.set_waveform_type(excitionchannel,waveform_type.sin)
            self.afg.set_waveform_type(synctrigger,waveform_type.square)
            self.afg.setChannelOutputState(synctrigger,1)
            self.afg.setChannelOutputState(excitionchannel,1)
            return
        else:
            self.osc.setChannelCouple(inputchannel,couple_type.ac)
            self.osc.setChannelCouple(outputchannel,couple_type.ac)
            self.osc.setChannelOffet(inputchannel,0)
            self.osc.setChannelOffet(outputchannel,0)
            self.osc.setAcquire(samplemode=samplemethod)

            self.osc.setTriggerChannel(inputchannel)
            self.osc.setTriggerLevel(0)

            self.afg.set_waveform_type(excitionchannel,waveform_type.sin)
            self.afg.setChannelOutputState(excitionchannel,1)
            return
    def setOSCChannel(self,inputchannel,outputchannel,\
                   syncchannel,samplemethod,averageTimes,freq):
        if(self.syncTriggerEnable == True):
            self.osc.setChannelCouple(inputchannel,couple_type.ac)
            self.osc.setChannelCouple(outputchannel,couple_type.ac)
            self.osc.setChannelCouple(syncchannel,couple_type.ac)
            self.osc.setChannelOffet(inputchannel,0)
            self.osc.setChannelOffet(outputchannel,0)
            self.osc.setChannelOffet(syncchannel,0)
            self.osc.setAcquire(samplemode=samplemethod)
            self.osc.setAverageTimes(averageTimes)
            self.osc.setTriggerChannel(syncchannel)
            self.osc.setTriggerLevel(0)
            self.osc.setTimebaseScale(0.25*1/freq)
            return
        else:
            self.osc.setChannelCouple(inputchannel,couple_type.ac)
            self.osc.setChannelCouple(outputchannel,couple_type.ac)
            self.osc.setChannelOffet(inputchannel,0)
            self.osc.setChannelOffet(outputchannel,0)
            self.osc.setAcquire(samplemode=samplemethod)

            self.osc.setTriggerChannel(inputchannel)
            self.osc.setTriggerLevel(0)
            self.osc.setTimebaseScale(0.25*1/freq)
            return

# -------------------- 主流程 --------------------
# Meas = load_device_class("Measurement", m_model)   # 测量类
# Exct = load_device_class("Excitation", e_model)    # 激励类

# # 演示：实例化并打印
# meas_inst = Meas()
# exct_inst = Exct()
# print("测量设备实例:", meas_inst)
# print("激励设备实例:", exct_inst)
if __name__=="__main__":
    args = parse_args()
    #arguments correction check
    m_model = args.m_device_model
    e_model = args.e_device_model
    m_tunnel = args.m_tunnel
    e_tunnel = args.e_tunnel
    m_addr = args.m_device_addr
    e_addr = args.e_device_addr
    uPyBode=PyBode(e_model,m_model,e_addr,m_addr,e_tunnel,m_tunnel)

    if(args.sync_trigger_enable == "true"):
        uPyBode.syncTriggerEnable = True
    if(args.no_gui == True):
        uPyBode.no_gui = True
    uPyBode.average_times=args.average_times
    excitionChannel=channel_number.ch1
    inputChannel=channel_number.ch1
    outputChannel=channel_number.ch2
    syncTrigger=channel_number.ch2
    syncChannel=channel_number.ch3
    sampleMethod = sample_method.normal
    for method in sample_method:
        if(args.sample_method.lower() == method.name):
            sampleMethod=method
    for channel in channel_number:
        if(args.excition_channel.lower() == channel.name):
            excitionChannel=channel
        if(args.input_channel.lower() == channel.name):
            inputChannel=channel
        if(args.output_channel.lower() == channel.name):
            outputChannel=channel
        if(args.sync_trigger.lower() == channel.name):
            syncTrigger=channel
        if(args.sync_channel.lower() == channel.name):
            syncChannel=channel

    uPyBode.setChannel(excitionChannel,inputChannel,outputChannel,\
                       syncTrigger,syncChannel,sampleMethod,args.average_times)

    uPyBode.run(args.startFreq,args.endFreq,args.points,args.amplitude\
                ,ExcitationChannel=excitionChannel,inputChannel=inputChannel,outputChannel=outputChannel,\
                syncTrigger=syncTrigger)
