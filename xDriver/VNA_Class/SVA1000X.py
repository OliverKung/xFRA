#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xDriver.py - VNA自动化测量工具
支持Siglent VNA设备的远程控制，测量双端口网络S参数并输出s2p文件
"""

import argparse
import socket
import time
import numpy as np
from datetime import datetime
import sys

class VNAController:
    def __init__(self, device_type, tunnel, address):
        """
        初始化VNA控制器
        
        Args:
            device_type: 设备类型 ('tcp' 或 'usb')
            tunnel: 连接隧道类型
            address: 设备地址 (IP地址或USB地址)
        """
        self.device_type = device_type
        self.tunnel = tunnel
        self.address = address
        self.socket = None
        self.is_connected = False
        
    def connect(self):
        """建立与VNA设备的连接"""
        try:
            if self.device_type == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.address, 5025))  # 默认端口5025
                self.socket.settimeout(10)
            else:
                # USB连接可以通过VISA或socket实现
                print(f"USB连接方式: {self.address}")
                return False
                
            self.is_connected = True
            print(f"成功连接到设备: {self.address}")
            return True
            
        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False
    
    def send_command(self, cmd):
        """发送SCPI命令到设备"""
        if not self.is_connected:
            print("设备未连接")
            return None
            
        try:
            if self.device_type == 'tcp':
                self.socket.send((cmd + '\n').encode())
                time.sleep(0.1)
                
                # 读取响应
                response = self.socket.recv(4096).decode().strip()
                return response
            else:
                print("USB命令发送未实现")
                return None
                
        except Exception as e:
            print(f"命令发送失败: {str(e)}")
            return None
    
    def configure_measurement(self, args):
        """配置VNA测量参数"""
        print("开始配置测量参数...")
        
        # 设置测量模式为双端口S参数
        self.send_command(":CALCulate1:PARameter:COUNt 4")  # 4个S参数
        self.send_command(":CALCulate1:PARameter1:DEFine S11")
        self.send_command(":CALCulate1:PARameter2:DEFine S21")
        self.send_command(":CALCulate1:PARameter3:DEFine S12")
        self.send_command(":CALCulate1:PARameter4:DEFine S22")
        
        # 设置频率范围
        self.send_command(f":SENSe1:FREQuency:STARt {args.start_freq}")
        self.send_command(f":SENSe1:FREQuency:STOP {args.stop_freq}")
        
        # 设置扫描点数
        self.send_command(f":SENSe1:SWEep:POINts {args.sweep_points}")
        
        # 设置中频带宽
        self.send_command(f":SENSe1:BWIDth {args.ifbw}")
        
        # 设置扫描类型
        if args.sweep_type == 'linear':
            self.send_command(":SENSe1:SWEep:TYPE LINEAR")
        elif args.sweep_type == 'log':
            self.send_command(":SENSe1:SWEep:TYPE LOGarithmic")
        
        # 设置源功率电平
        self.send_command(f":SOURce1:POWer {args.source_level}")
        
        # 设置平均次数
        self.send_command(f":SENSe1:AVERage:COUNt {args.averages}")
        if args.averages > 1:
            self.send_command(":SENSe1:AVERage:STATe ON")
        
        print("测量参数配置完成")
    
    def load_calibration(self, cal_file):
        """加载校准文件"""
        if cal_file:
            print(f"加载校准文件: {cal_file}")
            # 这里可以实现校准文件加载逻辑
            # self.send_command(f":MMEMory:LOAD CORRection, '{cal_file}'")
    
    def perform_measurement(self):
        """执行测量并获取数据"""
        print("开始执行测量...")
        
        # 触发单次扫描
        self.send_command(":INITiate1:IMMediate")
        
        # 等待测量完成
        time.sleep(2)  # 根据测量参数调整等待时间
        
        # 获取频率数据
        freq_data = self.send_command(":SENSe1:FREQuency:DATA?")
        
        # 获取各S参数数据
        s_params = {}
        
        # 选择每个参数并获取数据
        for i, param in enumerate(['S11', 'S21', 'S12', 'S22'], 1):
            self.send_command(f":CALCulate1:PARameter{i}:SELect")
            
            # 获取格式化数据 (实部和虚部)
            data = self.send_command(":CALCulate1:SELected:DATA:FDATa?")
            if data:
                # 解析数据 (格式: 实部1,虚部1,实部2,虚部2,...)
                values = [float(x) for x in data.split(',')]
                
                # 转换为复数形式
                complex_data = []
                for j in range(0, len(values), 2):
                    real_part = values[j]
                    imag_part = values[j+1]
                    complex_data.append(complex(real_part, imag_part))
                
                s_params[param] = np.array(complex_data)
        
        # 解析频率数据
        if freq_data:
            frequencies = [float(f) for f in freq_data.split(',')]
        else:
            # 如果没有频率数据，生成默认频率点
            num_points = len(s_params['S11'])
            start_freq = float(self.send_command(":SENSe1:FREQuency:STARt?"))
            stop_freq = float(self.send_command(":SENSe1:FREQuency:STOP?"))
            frequencies = np.linspace(start_freq, stop_freq, num_points)
        
        return frequencies, s_params
    
    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            self.is_connected = False
            print("设备连接已关闭")

class S2PWriter:
    """s2p文件写入器"""
    
    def __init__(self, filename):
        self.filename = filename
    
    def write(self, frequencies, s_params, args):
        """写入s2p格式文件"""
        try:
            with open(self.filename, 'w') as f:
                # 写入文件头
                f.write("# Hz S RI R 50\n")  # 频率单位Hz, S参数, 实部/虚部格式, 参考阻抗50Ω
                f.write(f"# Generated by xDriver on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Start Frequency: {args.start_freq} Hz\n")
                f.write(f"# Stop Frequency: {args.stop_freq} Hz\n")
                f.write(f"# Points: {len(frequencies)}\n")
                f.write(f"# IFBW: {args.ifbw} Hz\n")
                f.write(f"# Power: {args.source_level} dBm\n")
                f.write("!\n")  # 选项行结束符
                
                # 写入数据
                for i, freq in enumerate(frequencies):
                    s11 = s_params['S11'][i]
                    s21 = s_params['S21'][i]
                    s12 = s_params['S12'][i]
                    s22 = s_params['S22'][i]
                    
                    # 格式: 频率 S11实部 S11虚部 S21实部 S21虚部 S12实部 S12虚部 S22实部 S22虚部
                    f.write(f"{freq:.6e} {s11.real:.6e} {s11.imag:.6e} "
                           f"{s21.real:.6e} {s21.imag:.6e} "
                           f"{s12.real:.6e} {s12.imag:.6e} "
                           f"{s22.real:.6e} {s22.imag:.6e}\n")
            
            print(f"s2p文件已成功写入: {self.filename}")
            
        except Exception as e:
            print(f"写入s2p文件失败: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='VNA自动化测量工具')
    
    # 设备连接参数
    parser.add_argument('--device-type', required=True, choices=['tcp', 'usb'],
                       help='设备连接类型 (tcp 或 usb)')
    parser.add_argument('--device-tunnel', default='socket',
                       help='设备隧道类型')
    parser.add_argument('--device-address', required=True,
                       help='设备地址 (IP地址或USB地址)')
    
    # 测量参数
    parser.add_argument('--averages', type=int, default=1,
                       help='平均次数 (默认: 1)')
    parser.add_argument('--start-freq', type=float, required=True,
                       help='起始频率 (Hz)')
    parser.add_argument('--stop-freq', type=float, required=True,
                       help='终止频率 (Hz)')
    parser.add_argument('--sweep-type', choices=['linear', 'log'], default='linear',
                       help='扫描类型 (默认: linear)')
    parser.add_argument('--sweep-points', type=int, default=1601,
                       help='扫描点数 (默认: 1601)')
    parser.add_argument('--ifbw', type=float, default=1000,
                       help='中频带宽 (Hz, 默认: 1000)')
    parser.add_argument('--variable-amp', action='store_true',
                       help='启用可变幅度')
    parser.add_argument('--source-level', type=float, default=-10,
                       help='源功率电平 (dBm, 默认: -10)')
    
    # 校准和输出
    parser.add_argument('--calibration-file', type=str,
                       help='校准文件路径')
    parser.add_argument('--output-file', required=True,
                       help='输出s2p文件路径')
    
    args = parser.parse_args()
    
    # 验证参数
    if args.start_freq >= args.stop_freq:
        print("错误: 起始频率必须小于终止频率")
        sys.exit(1)
    
    if args.averages < 1:
        print("错误: 平均次数必须大于0")
        sys.exit(1)
    
    # 创建VNA控制器
    vna = VNAController(args.device_type, args.device_tunnel, args.device_address)
    
    try:
        # 连接设备
        if not vna.connect():
            print("无法连接到设备，程序退出")
            sys.exit(1)
        
        # 查询设备信息
        idn = vna.send_command("*IDN?")
        print(f"设备信息: {idn}")
        
        # 配置测量
        vna.configure_measurement(args)
        
        # 加载校准（如果提供）
        if args.calibration_file:
            vna.load_calibration(args.calibration_file)
        
        # 执行测量
        frequencies, s_params = vna.perform_measurement()
        
        # 写入s2p文件
        writer = S2PWriter(args.output_file)
        writer.write(frequencies, s_params, args)
        
        print("测量完成！")
        
    except KeyboardInterrupt:
        print("\n用户中断测量")
    except Exception as e:
        print(f"测量过程中发生错误: {str(e)}")
        sys.exit(1)
    finally:
        vna.close()

if __name__ == "__main__":
    main()