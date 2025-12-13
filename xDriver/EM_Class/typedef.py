
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

class channel_number(Enum):
    ch1="CHAN1"
    ch2="CHAN2"
    ch3="CHAN3"
    ch4="CHAN4"

class wave_parameter(Enum):
    Peak2Peak = "VPP"
    peak2peak = "VPP"
    rms = "VRMS"
    RMS = "VRMS"
    AVG = "VAVG"
    avg = "VAVG"

class signal_generator_channel_number(Enum):
    CH1="1"
    ch1="1"
    CH2="2"
    ch2="2"

class waveform_type(Enum):
    dc = "DC"
    pulse = "PULS"
    ramp = "RAMP"
    sin = "SIN"
    square = "SQU"
    triangle = "TRI"