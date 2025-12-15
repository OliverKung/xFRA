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
    parser.add_argument('--settling-time', type=float, default=0.0, help='Settling time after frequency change in seconds')
    return parser.parse_args()

# -------------------- 辅助函数 --------------------


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

    def setSettlingTime(self,settlingtime):
        self.settling_time = settlingtime

    def run(self,\
            ExcitationChannel:channel_number,\
            inputChannel:channel_number,\
            outputChannel:channel_number,\
            syncTrigger:channel_number,\
            unit:waveform_unit = waveform_unit.Vpp
            ):
        m_instru=self.m_instru
        e_instru=self.e_instru

        freq_list=self.freq_list
        amplitude_list=self.amplitude_list

        df=pd.DataFrame({}, columns=['freq', 'gain', 'phase'])

        m_instru.setTimebaseScale(10)
        counter = 1

        for freq in tqdm(freq_list):
            Ampilitude=amplitude_list[counter-1]
            counter = counter + 1
            # 设置频率和幅度
            e_instru.set_freq_amp(freq,Ampilitude,ExcitationChannel,unit)
            time.sleep(self.settling_time)
            # 设置同步触发时的方波频率
            if(self.syncTriggerEnable == True):
                freqSquare=freq
                while(freqSquare>e_instru.getMaxSquareWaveformFreq()):# 获取最大方波输出频率
                    freqSquare=freqSquare/2
                e_instru.set_freq_amp(freqSquare,1,syncTrigger)    #set signal source

            voltage1=m_instru.voltage(inputChannel,wave_parameter.RMS,freq)
            voltage2=m_instru.voltage(outputChannel,wave_parameter.RMS,freq)
            phase=m_instru.phase(inputChannel,outputChannel)

            gain=voltage2/voltage1
            # print("Freq: %.2f Hz, Gain: %.4f, Phase: %.2f deg"%(freq,gain,phase))
            # print("Input RMS Voltage: %.4f V, Output RMS Voltage: %.4f V"%(voltage1,voltage2))
            # 将数据添加到DataFrame中
            df.loc[len(df.index)]=[freq,gain,phase]
            # f.close()
        return df

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
    settling_time = args.settling_time # not set yet

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
    print("Sample Method:",sampleMethod)
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
    # -------- 设置激励单位 --------
    for unit in waveform_unit:
        if(source_amp_unit.upper() == unit.value):
            sourceUnit=unit

    # -------- 设置通道参数 --------
    uPyBode.setChannel(excitionChannel,inputChannel,outputChannel,\
                       syncTrigger,syncChannel,sampleMethod,average_sample_times)
    uPyBode.generate_freq_sourcelevel_list(start_freq,end_freq,sweep_type,sweep_points,source_amp,variable_amp,variable_amp_freq)
    uPyBode.setSettlingTime(settling_time)
    uPyBode.setOutputFile(output_file)
    print("Starting measurement...")
    print("Average Measurement Times:",average)
    # 运行n次测试取平均
    data = uPyBode.run(\
            excitionChannel,\
            inputChannel,\
            outputChannel,\
            syncTrigger,\
            sourceUnit
        )
    for i in range(average-1):
        print(f"Starting average run {i+2} of {average}...")
        data += uPyBode.run(\
            excitionChannel,\
            inputChannel,\
            outputChannel,\
            syncTrigger,\
            sourceUnit
        )
    data = data / average
    # 以S2P的格式保存数据到文件,按照S11 S21 S12 S22的格式保存，其中，S11和S22的幅度为1，相位为0，S21和S12的幅度和相位由测量结果决定
    print("Saving data to file:",output_file)
    with open(output_file,"w") as f:
        f.write("! Touchstone file generated by xDrvEM.py\n")
        f.write("# Hz S RI R 50\n")
        f.write("! Hz ReS11 ImS11 ReS21 ImS21 ReS12 ImS12 ReS22 ImS22\n")
        for index,row in data.iterrows():
            freq=row['freq']
            gain=row['gain']
            phase=row['phase']
            ReS21=gain*math.cos(math.radians(phase))
            ImS21=gain*math.sin(math.radians(phase))
            ReS12=ReS21
            ImS12=ImS21
            f.write(f"{freq:.6f} 1.0000 0.0000 {ReS21:.6f} {ImS21:.6f} {ReS12:.6f} {ImS12:.6f} 1.0000 0.0000\n")
        