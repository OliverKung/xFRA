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
from typedef import *
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
    parser.add_argument('--variable-amp', nargs='+', help='Enable variable source amplitude')
    parser.add_argument('--variable-amp-freq', nargs='+', help='Enable variable source amplitude frequency')
    parser.add_argument('--source-amp', type=float, default=-10.0, help='Source amplitude in dBm')
    parser.add_argument('--source-amp-unit', type=str, default='dBm', help='Source amplitude unit (dBm or Vpp)')
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
        self.freq_list = []
        self.amplitude_list = []
        self.average_times = 4
        self.output_file = ""

    def generate_freq_sourcelevel_list(self,startFreq,stopFreq,sweep_type,totalPoints,source_amp,variable_amp = None,variable_amp_freq = None):
        if sweep_type.upper() == "LIN":
            freq_list=np.linspace(startFreq,stopFreq,int(totalPoints),endpoint = True)
        elif sweep_type.upper() == "LOG":
            freq_list=np.logspace(math.log(startFreq,10),math.log(stopFreq,10),int(totalPoints),endpoint = True)
        else:
            print("Sweep type error, only LIN and LOG are supported.")
            return
        self.freq_list = freq_list
        if(variable_amp != None and variable_amp_freq != None):
            amp_list = []
            # 输入的variable_amp_freq和variable_amp是字符串列表，需要转换为float列表
            variable_amp_freq = [float(i) for i in variable_amp_freq]
            variable_amp = [float(i) for i in variable_amp]
            for freq in freq_list:
                # 查找当前频率对应的幅度
                if freq <= variable_amp_freq[0]:
                    amp_list.append(variable_amp[0])
                elif freq >= variable_amp_freq[-1]:
                    amp_list.append(variable_amp[-1])
                else:
                    for i in range(1, len(variable_amp_freq)):
                        if variable_amp_freq[i-1] < freq <= variable_amp_freq[i]:
                            # 线性插值计算幅度
                            slope = (variable_amp[i] - variable_amp[i-1]) / (variable_amp_freq[i] - variable_amp_freq[i-1])
                            amp = variable_amp[i-1] + slope * (freq - variable_amp_freq[i-1])
                            amp_list.append(amp)
                            break
            self.amplitude_list = amp_list
        else:
            self.amplitude_list = [source_amp]*len(freq_list)
    
    def setOutputFile(self,outputfile):
        self.output_file = outputfile

    def run(self,\
            ExcitationChannel:channel_number,\
            inputChannel:channel_number,\
            outputChannel:channel_number,\
            syncTrigger:channel_number,\
            ):
        m_instru=self.m_instru
        e_instru=self.e_instru

        freq_list=self.freq_list
        amplitude_list=self.amplitude_list
        totalPoints=len(freq_list)

        df=pd.DataFrame({}, columns=['freq', 'gain', 'phase'])

        m_instru.setTimebaseScale(10)

        # 读取初始状态的量程和衰减
        channel1_scale=m_instru.getChannelScale(inputChannel)
        channel2_scale=m_instru.getChannelScale(outputChannel)
        counter = 1

        channel1_atte = m_instru.getChannelAtte(inputChannel)
        channel2_atte = m_instru.getChannelAtte(outputChannel)
        filename=self.output_file
        with open(".\\temp\\datafilename.txt","w") as f:
            f.write(filename)
        with open(".\\ExampleData\\"+filename,"w") as f:
            for freq in tqdm(freq_list):
                Ampilitude=amplitude_list[counter-1]
                counter = counter + 1
                # 设置计算采样延时
                if(self.syncTriggerEnable == False):
                    sample_delay=0.1 if 0.1>4*1/freq*2**self.average_times else 4*1/freq*2**self.average_times
                else:
                    sample_delay=1 if 0.1>6*4*1/freq*2**self.average_times else 6*4*1/freq*2**self.average_times
                # 设置频率和幅度
                e_instru.set_freq_amp(freq,Ampilitude,ExcitationChannel)
                # 设置同步触发时的方波频率
                if(self.syncTriggerEnable == True):
                    freqSquare=freq
                    while(freqSquare>e_instru.getMaxSquareWaveformFreq()):# 获取最大方波输出频率
                        freqSquare=freqSquare/2
                    e_instru.set_freq_amp(freqSquare,1,syncTrigger)    #set signal source
            
                # 设置示波器时间幅度
                m_instru.setTimebaseScale(0.25*1/freq)

                # 等待测量稳定
                time.sleep(sample_delay)
                
                # 读取电压值
                voltage1=m_instru.voltage(inputChannel,wave_parameter.Peak2Peak)
                voltage2=m_instru.voltage(outputChannel,wave_parameter.Peak2Peak)
                loopCounter = 0

                #自动缩放调整幅度
                while(voltage1>channel1_scale*8 and loopCounter<max_try_times):#When amplitude is too large, auto scale
                    print("CH1 voltage scale too large, voltage is "+str(voltage1)+",scale is "+str(channel1_scale)+", Freq is "+str(freq))
                    m_instru.setChannelScale(inputChannel,channel1_scale*8)
                    time.sleep(sample_delay)
                    channel1_scale=channel1_scale*8
                    channel1_scale = voltageScaleLimiter(channel1_scale,channel1_atte,freq)
                    voltage1=m_instru.voltage(inputChannel,wave_parameter.Peak2Peak)
                    loopCounter=loopCounter+1
                
                if loopCounter==max_try_times:
                    m_instru.autoscale()
                    self.setOSCChannel(inputChannel,outputChannel,self.syncChannel,self.sample_method,self.average_times,freq)
                    print(channel1_scale)
                    channel1_scale=m_instru.getChannelScale(inputChannel)
                    print(channel1_scale)

                loopCounter = 0
                while(voltage2>channel2_scale*8 and loopCounter<max_try_times):#When amplitude is too large, auto scale
                    print("CH2 voltage scale too large, voltage is "+str(voltage2)+",scale is "+str(channel2_scale)+", Freq is "+str(freq))
                    m_instru.setChannelScale(outputChannel,channel2_scale*8)
                    time.sleep(sample_delay)
                    channel2_scale=channel2_scale*8
                    channel2_scale = voltageScaleLimiter(channel2_scale,channel2_atte,freq)
                    voltage2=m_instru.voltage(outputChannel,wave_parameter.Peak2Peak)
                    print(voltage2)
                    loopCounter=loopCounter+1
                
                if loopCounter==max_try_times:
                    m_instru.autoscale()
                    self.setOSCChannel(inputChannel,outputChannel,self.syncChannel,self.sample_method,self.average_times,freq)
                    print(channel2_scale)
                    channel2_scale=m_instru.getChannelScale(outputChannel)
                    print(channel2_scale)
                    time.sleep(5)

                loopCounter = 0
                while((voltage1<2*channel1_scale or voltage1>6*channel1_scale) and loopCounter<max_try_times):
                    time.sleep(sample_delay)
                    voltage1=m_instru.voltage(inputChannel,wave_parameter.Peak2Peak)
                    if(voltage1>1e10):
                        voltage1=m_instru.voltage(inputChannel,wave_parameter.rms)*4*1.414
                    channel1_scale = voltageScaleLimiter(voltage1/4,channel1_atte,freq)
                    m_instru.setChannelScale(inputChannel,channel1_scale)#AutoScale when signal is too small
                    loopCounter = loopCounter+1
                loopCounter = 0
                while((voltage2<2*channel2_scale or voltage2>6*channel2_scale) and loopCounter<max_try_times):
                    time.sleep(sample_delay)
                    voltage2=m_instru.voltage(outputChannel,wave_parameter.Peak2Peak)
                    if(voltage2>1e10):
                        voltage2=m_instru.voltage(inputChannel,wave_parameter.rms)*4*1.414
                    channel2_scale = voltageScaleLimiter(voltage2/4,channel2_atte,freq)
                    m_instru.setChannelScale(outputChannel,channel2_scale)
                    loopCounter = loopCounter+1

                time.sleep(sample_delay) #wait for measure

                voltage1=m_instru.voltage(inputChannel,wave_parameter.RMS)

                time.sleep(sample_delay)
                voltage2=m_instru.voltage(outputChannel,wave_parameter.RMS)
                print("freq:",freq)
                print("voltage1:",voltage1)
                print("voltage2:",voltage2)
                phase=-1*m_instru.phase(inputChannel,outputChannel)
                while(phase>360 or phase <-360):
                    phase=-1*m_instru.phase(inputChannel,outputChannel)
                loopCounter = 0
                while(phase > 180 or phase<-180 and loopCounter<max_try_times):
                    phase=-1*m_instru.phase(inputChannel,outputChannel)
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
            self.m_instru.setChannelCouple(inputchannel,couple_type.ac)
            self.m_instru.setChannelCouple(outputchannel,couple_type.ac)
            self.m_instru.setChannelCouple(syncchannel,couple_type.ac)
            self.m_instru.setChannelOffet(inputchannel,0)
            self.m_instru.setChannelOffet(outputchannel,0)
            self.m_instru.setChannelOffet(syncchannel,0)
            self.m_instru.setAcquire(samplemode=samplemethod)
            self.m_instru.setAverageTimes(averageTimes)
            self.m_instru.setTriggerChannel(syncchannel)
            self.m_instru.setTriggerLevel(0)

            self.e_instru.set_waveform_type(excitionchannel,waveform_type.sin)
            self.e_instru.set_waveform_type(synctrigger,waveform_type.square)
            self.e_instru.setChannelOutputState(synctrigger,1)
            self.e_instru.setChannelOutputState(excitionchannel,1)
            return
        else:
            self.m_instru.setChannelCouple(inputchannel,couple_type.ac)
            self.m_instru.setChannelCouple(outputchannel,couple_type.ac)
            self.m_instru.setChannelOffet(inputchannel,0)
            self.m_instru.setChannelOffet(outputchannel,0)
            self.m_instru.setAcquire(samplemode=samplemethod)

            self.m_instru.setTriggerChannel(inputchannel)
            self.m_instru.setTriggerLevel(0)

            self.e_instru.set_waveform_type(excitionchannel,waveform_type.sin)
            self.e_instru.setChannelOutputState(excitionchannel,1)
            return
    def setOSCChannel(self,inputchannel,outputchannel,\
                   syncchannel,samplemethod,averageTimes,freq):
        if(self.syncTriggerEnable == True):
            self.m_instru.setChannelCouple(inputchannel,couple_type.ac)
            self.m_instru.setChannelCouple(outputchannel,couple_type.ac)
            self.m_instru.setChannelCouple(syncchannel,couple_type.ac)
            self.m_instru.setChannelOffet(inputchannel,0)
            self.m_instru.setChannelOffet(outputchannel,0)
            self.m_instru.setChannelOffet(syncchannel,0)
            self.m_instru.setAcquire(samplemode=samplemethod)
            self.m_instru.setAverageTimes(averageTimes)
            self.m_instru.setTriggerChannel(syncchannel)
            self.m_instru.setTriggerLevel(0)
            self.m_instru.setTimebaseScale(0.25*1/freq)
            return
        else:
            self.m_instru.setChannelCouple(inputchannel,couple_type.ac)
            self.m_instru.setChannelCouple(outputchannel,couple_type.ac)
            self.m_instru.setChannelOffet(inputchannel,0)
            self.m_instru.setChannelOffet(outputchannel,0)
            self.m_instru.setAcquire(samplemode=samplemethod)

            self.m_instru.setTriggerChannel(inputchannel)
            self.m_instru.setTriggerLevel(0)
            self.m_instru.setTimebaseScale(0.25*1/freq)
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
    m_model = args.m_device_model   # set during init
    e_model = args.e_device_model   # set during init
    m_tunnel = args.m_device_tunnel # set during init
    e_tunnel = args.e_device_tunnel # set during init
    m_addr = args.m_device_addr     # set during init
    e_addr = args.e_device_addr     # set during init

    average_sample_times = args.average_sample_times

    average = args.average          # set during PyBode run 
    start_freq = args.start_freq    # set during PyBode run
    end_freq = args.end_freq        # set during PyBode run
    sweep_type = args.sweep_type    # set during PyBode run
    sweep_points = args.sweep_points# set during PyBode run

    ifbw = args.ifbw                # not set yet
    variable_amp = args.variable_amp# not set yet
    variable_amp_freq = args.variable_amp_freq# not set yet
    source_amp = args.source_amp# set during PyBode run
    source_amp_unit = args.source_amp_unit# set during PyBode run
    calibration = args.calibration  # not set yet
    output_file = args.output_file  # not set yet
    sample = args.sample_method     # set during PyBode run
    excition_channel = args.excition_channel # set during PyBode run and setChannel
    input_channel = args.input_channel # set during PyBode run and setChannel
    output_channel = args.output_channel # set during PyBode run and setChannel
    sync_trigger = args.sync_trigger # set during PyBode run and setChannel
    sync_channel = args.sync_channel # set during PyBode run and setChannel
    sync_trigger_enable = args.sync_trigger_enable # set during PyBode run and setChannel

    uPyBode=PyBode(e_model,m_model,e_addr,m_addr,e_tunnel,m_tunnel)

    if(args.sync_trigger_enable == "true"):
        uPyBode.syncTriggerEnable = True
    uPyBode.average_times=average_sample_times
    excitionChannel=channel_number.ch1
    inputChannel=channel_number.ch1
    outputChannel=channel_number.ch2
    syncTrigger=channel_number.ch2
    syncChannel=channel_number.ch3
    sampleMethod = sample_method.normal
    # -------- 设置采样方法 --------
    for method in sample_method:
        if(args.sample_method.lower() == method.name):
            sampleMethod=method
    # -------- 设置通道号 --------
    for channel in channel_number:
        if(excition_channel.lower() == channel.name):
            excitionChannel=channel
        if(input_channel.lower() == channel.name):
            inputChannel=channel
        if(output_channel.lower() == channel.name):
            outputChannel=channel
        if(sync_trigger.lower() == channel.name):
            syncTrigger=channel
        if(sync_channel.lower() == channel.name):
            syncChannel=channel

    uPyBode.setChannel(excitionChannel,inputChannel,outputChannel,\
                       syncTrigger,syncChannel,sampleMethod,args.average_times)

    uPyBode.run(start_freq,end_freq,sweep_points,source_amp\
                ,ExcitationChannel=excitionChannel,inputChannel=inputChannel,outputChannel=outputChannel,\
                syncTrigger=syncTrigger)
