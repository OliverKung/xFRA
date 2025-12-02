#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s2p_ri_convert.py
自动读取指定 s2p 文件，并把数据统一转换成实部+虚部（RI）格式后写回。
用法:
    python s2p_ri_convert.py  your_file.s2p
"""
import sys
import re
import pathlib
import numpy as np

# ---------- 工具函数 ----------
def _parse_format_line(line: str):
    """
    解析 Touchstone 选项行，返回 (freq_unit, parameter, format, Z0)
    例如 '# GHz S MA R 50' -> ('GHz', 'S', 'MA', 50.0)
    """
    line = line.strip().upper()
    if not line.startswith('#'):
        raise ValueError("Not a valid option line")
    tokens = line[1:].split()
    if len(tokens) < 4:
        raise ValueError("Option line too short")
    freq_unit = tokens[0]
    param     = tokens[1]
    fmt       = tokens[2]
    z0        = float(tokens[4]) if len(tokens) > 4 else 50.0
    return freq_unit, param, fmt, z0

def _sniff_touchstone_version(file):
    """
    简单判断是 v1 还是 v2：
    v2 文件开头会出现 [Version] 字段。
    """
    pos = file.tell()
    first_lines = file.read(800)
    file.seek(pos)
    return b'[Version]' in first_lines

def _read_v1(file, encoding='utf-8'):
    """
    读取 Touchstone v1 格式，返回
    freq, data, option_line, comments
    data 形状 (n_freq, n_ports, n_ports) 复数矩阵
    """
    comments = []
    option_line = None
    while True:
        line = file.readline().decode(encoding).strip()
        if not line:
            continue
        if line.startswith('!'):
            comments.append(line)
            continue
        if line.startswith('#'):
            option_line = line
            break
        # 无效行直接跳过
    if option_line is None:
        raise ValueError("Missing '#' option line")

    freq_unit, param, fmt, z0 = _parse_format_line(option_line)
    if param != 'S':
        raise NotImplementedError("Only S-parameter supported")
    # 收集所有数据行
    data_lines = []
    for line in file:
        line = line.decode(encoding).strip()
        if line == '' or line.startswith('!'):
            continue
        data_lines.append(line)
    raw = np.loadtxt(data_lines)   # 第一列为频率
    freq = raw[:, 0]
    n_ports = int(np.sqrt((raw.shape[1] - 1) / 2))
    n_freq  = freq.size
    # 按格式转成复数
    if fmt == 'RI':
        values = raw[:, 1:].view(dtype=np.complex128).reshape((n_freq, n_ports, n_ports))
    elif fmt == 'MA':
        mag  = raw[:, 1::2]
        ang  = raw[:, 2::2]
        values = (mag * np.exp(1j * ang * np.pi / 180.0)).reshape((n_freq, n_ports, n_ports))
    elif fmt == 'DB':
        db   = raw[:, 1::2]
        ang  = raw[:, 2::2]
        mag  = 10**(db / 20.0)
        values = (mag * np.exp(1j * ang * np.pi / 180.0)).reshape((n_freq, n_ports, n_ports))
    else:
        raise ValueError(f"Unknown format {fmt}")
    return freq, values, option_line, comments, z0

def _write_v1(fname, freq, data, option_line, comments, z0):
    """
    把 data 以 RI 格式写回 v1 文件
    """
    n_freq, n_ports, _ = data.shape
    # 构造新的 option line
    tokens = option_line.upper().split()
    tokens[2] = 'RI'   # 强制改成 RI
    new_opt = '# ' + ' '.join(tokens)
    with open(fname, 'w', encoding='utf-8') as f:
        for c in comments:
            f.write(c + '\n')
        f.write(new_opt + '\n')
        for i in range(n_freq):
            f.write(f'{freq[i]:.10e} ')
            # 按行优先写 n_ports x n_ports
            for r in range(n_ports):
                for c in range(n_ports):
                    z = data[i, r, c]
                    f.write(f'{z.real:.10e} {z.imag:.10e} ')
            f.write('\n')

# ---------- 主流程 ----------
def convert_s2p_to_ri(src: pathlib.Path):
    dst = src.with_name(src.stem + '_RI' + src.suffix)
    with open(src, 'rb') as f:
        is_v2 = _sniff_touchstone_version(f)
    if is_v2:
        # 这里仅演示 v1，v2 可类似解析矩阵块后做同样转换
        raise NotImplementedError("Touchstone v2 解析未在本示例中实现，可手动扩展")
    # 按 v1 读取
    with open(src, 'rb') as f:
        freq, data, opt, cmt, z0 = _read_v1(f)
    # 写回
    _write_v1(dst, freq, data, opt, cmt, z0)
    print(f'Converted -> {dst}')

# ---------- 入口 ----------
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python s2p_ri_convert.py  your_file.s2p')
        sys.exit(1)
    file_path = pathlib.Path(sys.argv[1]).expanduser()
    if not file_path.is_file():
        print(f'File not found: {file_path}')
        sys.exit(2)
    convert_s2p_to_ri(file_path)