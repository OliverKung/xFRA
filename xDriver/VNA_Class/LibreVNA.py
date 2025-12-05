# xDrviver/VNA_Class/LibreVNA.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# xDrvSetting begin
# device-type VNA
# model LibreVNA
# tunnel SCPI socket
# average yes
# min-freq 100000
# max-freq 6000000000
# sweep-type LOG LIN
# sweep-points 2 65535
# ifbw 6 100 200 500 1000 2000 5000 10000 20000 50000 100000 200000 500000
# variable-amp no
# source-level -40 0
# level-unit dBm
# Receiver1Attn 0
# Receiver2Attn 0
# xDrvSetting end
#python LibreVNA.py --device-address 192.168.1.100 --start-freq 1e6 --stop-freq 1e9 --sweep-type LIN --sweep-points 501 --ifbw 1e3 --source-level -10 --averages 3 --output-file meas.s2p
"""
LibreVNA SCPI-driver
用法与 SVA1000X.py 完全一致，直接替换即可。
"""
import argparse
import sys
import time
import socket
import json
import numpy as np

# ---------- 工具函数 ----------
def scpi_cmd(sock, cmd):
    """发送一条 SCPI 命令，自动补 \\n"""
    sock.send((cmd.rstrip() + "\n").encode())

def scpi_query(sock, cmd, timeout=20):
    """发送查询并返回去尾字符串"""
    sock.settimeout(timeout)
    scpi_cmd(sock, cmd)
    # 返回所有数据
    data = b""
    while True:
        chunk = sock.recv(4096)
        data += chunk
        if len(chunk) < 4096:
            break
    return data.decode().strip()

def connect_scpi(addr, port=19542):
    """返回已连接的 socket"""
    s = socket.create_connection((addr, port), timeout=5)
    # 先清一次欢迎信息（如有）
    s.settimeout(0.5)
    try:
        _ = s.recv(4096)
    except socket.timeout:
        pass
    return s

# ---------- 参数解析（与 SVA1000X.py 完全一致） ----------
def parse_arguments():
    parser = argparse.ArgumentParser(description="LibreVNA S2P Measurement Driver")
    parser.add_argument("--device-tunnel", default="SCPI", help="Connection tunnel type")
    parser.add_argument("--device-address", required=True,
                        help="SCPI address: ip:port 或仅 ip（默认 19542）")
    parser.add_argument("--averages", type=int, default=1, help="Number of averages")
    parser.add_argument("--start-freq", type=float, required=True, help="Start frequency in Hz")
    parser.add_argument("--stop-freq", type=float, required=True, help="Stop frequency in Hz")
    parser.add_argument("--sweep-type", default="LIN", choices=["LIN", "LOG"], help="Sweep type")
    parser.add_argument("--sweep-points", type=int, default=201, help="Number of sweep points")
    parser.add_argument("--ifbw", type=float, default=1000, help="IF Bandwidth in Hz")
    parser.add_argument("--variable-amp", help="Reserved")
    parser.add_argument("--source-level", type=float, default=-10, help="Source power in dBm")
    parser.add_argument("--calibration", help="Local cal file to load (*.cal)")
    parser.add_argument("--output-file", required=True, help="Output .s2p file")
    return parser.parse_args()

# ---------- 仪器配置 ----------
def configure_instrument(sock, args):
    scpi_cmd(sock, "*CLS")
    idn = scpi_query(sock, "*IDN?")
    print(f"Connected to: {idn}")

    # 1. 切换到 VNA 模式
    scpi_cmd(sock, "DEV:MODE VNA")
    time.sleep(1)

    # 2. 频率
    scpi_cmd(sock, f"VNA:FREQ:START {args.start_freq}")
    scpi_cmd(sock, f"VNA:FREQ:STOP {args.stop_freq}")

    # 3. 功率
    scpi_cmd(sock, f"VNA:STIM:LVL {args.source_level}")

    # 4. 带宽、点数、扫描类型
    scpi_cmd(sock, f"VNA:ACQ:IFBW {args.ifbw}")
    scpi_cmd(sock, f"VNA:ACQ:POINTS {args.sweep_points}")
    scpi_cmd(sock, f"VNA:SWEEPTYPE {args.sweep_type}")

    # 5. 平均
    if args.averages > 1:
        scpi_cmd(sock, f"VNA:ACQ:AVG {args.averages}")
        scpi_cmd(sock, "VNA:ACQ:AVG ON")
    else:
        scpi_cmd(sock, "VNA:ACQ:AVG OFF")

    # 6. 校准（若指定）
    if args.calibration:
        print(f"Loading calibration: {args.calibration}")
        scpi_cmd(sock, f"VNA:CAL:LOAD \"{args.calibration}\"")
        scpi_cmd(sock, "VNA:CAL:ACT")

    # 7. 创建 4 条迹线用于 S11/S21/S12/S22
    scpi_cmd(sock, "VNA:TRAC:DEL ALL")          # 清空旧迹线
    for name, param in zip(("S11", "S21", "S12", "S22"),
                           ("S11", "S21", "S12", "S22")):
        scpi_cmd(sock, f"VNA:TRAC:NEW {name}")
        scpi_cmd(sock, f"VNA:TRAC:PARAM {name} {param}")
    print("Instrument configured.")

# ---------- 测量 ----------
def perform_measurement(sock):
    print("Performing measurement...")
    scpi_cmd(sock, "VNA:ACQ:SINGLE TRUE")   # 单次扫描
    scpi_cmd(sock, "*WAI")                  # 等待完成

def retrieve_data(sock):
    """返回 dict: {'s11':[re,im,...], 's21':[], 's12':[], 's22':[]}"""
    print("Retrieving trace data...")
    s_params = {}
    for tr in ("S11", "S21", "S12", "S22"):
        raw = scpi_query(sock, f"VNA:TRAC:DATA? {tr}")
        # LibreVNA 返回:  [freq, re, im], [freq, re, im], ...
        pairs = [ln.split(',') for ln in raw.strip('[]').split('],[')]
        values = []
        for p in pairs:
            values.extend([float(p[1]), float(p[2])])  # re, im
        s_params[tr.lower()] = values
    return s_params

# ---------- S2P 写入（与 SVA1000X.py 完全一致） ----------
def write_s2p(filename, freqs, s_data):
    print(f"Exporting to {filename}...")
    with open(filename, 'w') as f:
        f.write("! Touchstone file generated by LibreVNA.py\n")
        f.write("# Hz S RI R 50\n")
        f.write("! Freq ReS11 ImS11 ReS21 ImS21 ReS12 ImS12 ReS22 ImS22\n")
        n = len(freqs)
        for i in range(n):
            idx = i * 2
            line = f"{freqs[i]:.6e} "
            line += f"{s_data['s11'][idx]:.6f} {s_data['s11'][idx+1]:.6f} "
            line += f"{s_data['s21'][idx]:.6f} {s_data['s21'][idx+1]:.6f} "
            line += f"{s_data['s12'][idx]:.6f} {s_data['s12'][idx+1]:.6f} "
            line += f"{s_data['s22'][idx]:.6f} {s_data['s22'][idx+1]:.6f}\n"
            f.write(line)

# ---------- 主函数 ----------
def main():
    args = parse_arguments()
    # 解析地址
    if ':' in args.device_address:
        ip, port = args.device_address.split(':', 1)
        port = int(port)
    else:
        ip, port = args.device_address, 19542

    sock = connect_scpi(ip, port)
    try:
        configure_instrument(sock, args)

        if args.averages > 1:
            s_acc = None
            for i in range(args.averages):
                print(f"Acquisition {i+1}/{args.averages}")
                perform_measurement(sock)
                d = retrieve_data(sock)
                print("Data retrieved.", d)
                if s_acc is None:
                    s_acc = d
                else:
                    for k in s_acc:
                        s_acc[k] = [a + b for a, b in zip(s_acc[k], d[k])]
            s_data = {k: [v / args.averages for v in s_acc[k]] for k in s_acc}
        else:
            perform_measurement(sock)
            s_data = retrieve_data(sock)

        # 生成频率列表
        if args.sweep_type == "LIN":
            if args.sweep_points > 1:
                step = (args.stop_freq - args.start_freq) / (args.sweep_points - 1)
                freqs = [args.start_freq + i * step for i in range(args.sweep_points)]
            else:
                freqs = [args.start_freq]
        else:
            freqs = np.logspace(np.log10(args.start_freq),
                                np.log10(args.stop_freq),
                                args.sweep_points).tolist()

        write_s2p(args.output_file, freqs, s_data)
        print("Done.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()