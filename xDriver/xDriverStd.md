# xDriver标准文件
## 直接测量FRA的频域仪器
- device-type 设备的种类，暂时分为VNA
- device-tunnel 设备的通讯协议，暂时分为socket、serial、GPIB、LXI11
- device-address 设备的地址，根据上文的socket选择
- average 平均测量次数

- start-freq 起始频率
- end-freq 终止频率
- sweep-type 扫频方法，可选线性或对数
- sweep-point 扫频点数

- bandwidt 中频带宽

- variable-amp 可变激励幅度开关
- source-level 激励幅度，当可变开关打开时，输入n个频率 幅度点对，实现可变幅度

- calibration 校准文件路径

## Excitation-Measurement Class（E-M类）
python xDrvEM.py --m-device-model tcp --device-address 192.168.1.119 --averages 1 --start-freq 1000000 --stop-freq 1000000000 --sweep-type log --sweep-points 101 --ifbw 1000 --source-level -10 --output-file measurement.s2p
- m-device-model M器件的型号
- m-device-tunnel M设备的通讯协议，暂时分为socket、serial、GPIB、LXI11
- m-device-address M设备的地址，根据上文的socket选择

- e-device-model E器件的型号
- e-device-tunnel E设备的通讯协议，暂时分为socket、serial、GPIB、LXI11
- e-device-address E设备的地址，根据上文的socket选择

- average 平均测量次数

- start-freq 起始频率
- end-freq 终止频率
- sweep-type 扫频方法，可选线性或对数
- sweep-point 扫频点数

- bandwidt 中频带宽

- variable-amp 可变激励幅度开关
- source-level 激励幅度，当可变开关打开时，输入n个频率 幅度点对，实现可变幅度

- calibration 校准文件路径

### Excitation类需要实现的标准函数
- setFreqAmp(freq,amplitude,channel,unit)
- setWaveformType(channel,waveform)
- setChannelOutputState(channel,state)
- setChannelLoadImpedance(channel,loadimpedance)
- getMaxSquareFreq()
- getAmpUnit()

### Measurement类需要实现的标准函数
#### 测量类
- autoscale()
- voltage(channel,items)
- freq(channel)
- phase(channelA,channelB)
#### 设置类
- setSampleMode(samplemode)
- setChannelCouple(channel,couple)
- setTriggerChannel(channel)
- setAverageTimes(averagetimes)
- setChannelAtte(channel,atte)
- setChannelUnit(channel,unit)
- setSynctrigger(state)
#### 回读类
- getSampleDelay(freq,syntriggerEnable)

