#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s2p_ri_convert.py
读取任意 *.s2p（v1） → 统一转成实部/虚部（RI） → 写回新文件
修正点：
1. 严格解析频率单位，把频率列转换成 Hz 存储；
2. 写回时按原单位还原；
3. 保留原 option line 其余字段（参数、参考阻抗、注释）。
"""
import sys
import pathlib
import numpy as np

# ---------- 工具 ----------
FREQ_MUL = {'HZ': 1.0, 'KHZ': 1e3, 'MHZ': 1e6, 'GHZ': 1e9}

def _parse_option(line: str):
    """
    解析 '# GHz S MA R 50'
    返回 (freq_unit, param, fmt, z0, mul)
    mul 是把频率变成 Hz 的乘数
    """
    line = line.strip().upper()
    if not line.startswith('#'):
        raise ValueError('Not an option line')
    tok = line[1:].split()
    if len(tok) < 4:
        raise ValueError('Option line too short')
    freq_unit = tok[0]
    mul = FREQ_MUL.get(freq_unit)
    if mul is None:
        raise ValueError(f'Unknown frequency unit {freq_unit}')
    param, fmt, z0 = tok[1], tok[2], float(tok[4]) if len(tok) > 4 else 50.0
    return freq_unit, param, fmt, z0, mul

def _read_v1(file):
    """返回 (freq_hz, data, option_line, comments, freq_unit, z0)"""
    comments, opt_line = [], None
    for raw in file:
        line = raw.decode('utf-8').strip()
        if line.startswith('!'):
            comments.append(line); continue
        if line.startswith('#'):
            opt_line = line; break
    if opt_line is None:
        raise ValueError('Missing option line')
    freq_unit, param, fmt, z0, mul = _parse_option(opt_line)
    if param != 'S':
        raise NotImplementedError('Only S-param supported')
    # 收集数据行
    blk = []
    for raw in file:
        line = raw.decode('utf-8').strip()
        if line and not line.startswith('!'):
            blk.append(line)
    raw = np.loadtxt(blk)
    freq_hz = raw[:, 0] * mul   # 统一转成 Hz
    n_ports = int(np.sqrt((raw.shape[1] - 1) // 2))
    if fmt == 'RI':
        cplx = raw[:, 1:].view(np.complex128).reshape((-1, n_ports, n_ports))
    elif fmt == 'MA':
        mag, ang = raw[:, 1::2], raw[:, 2::2]
        cplx = (mag * np.exp(1j * ang * np.pi / 180.0)).reshape((-1, n_ports, n_ports))
    elif fmt == 'DB':
        db, ang = raw[:, 1::2], raw[:, 2::2]
        mag = 10**(db / 20.0)
        cplx = (mag * np.exp(1j * ang * np.pi / 180.0)).reshape((-1, n_ports, n_ports))
    else:
        raise ValueError(f'Unknown format {fmt}')
    return freq_hz, cplx, opt_line, comments, freq_unit, z0

def _write_v1(fname, freq_hz, data, old_opt, comments, freq_unit, z0):
    """写回 v1，频率按原单位输出"""
    inv_mul = 1.0 / FREQ_MUL[freq_unit]
    # 构造新 option line，仅把格式改成 RI
    tok = old_opt.upper().split()
    tok[2] = 'RI'
    new_opt = ' '.join(tok)          # ←←← 这里去掉前面的 '#'
    n_ports = data.shape[2]
    with open(fname, 'w', encoding='utf-8') as f:
        for c in comments:
            f.write(c + '\n')
        f.write(new_opt + '\n')  # ←←← 只在这一处统一加 '# '
        for i, fr in enumerate(freq_hz):
            f.write(f'{fr * inv_mul:.10e} ')
            for r in range(n_ports):
                for c in range(n_ports):
                    z = data[i, r, c]
                    f.write(f'{z.real:.10e} {z.imag:.10e} ')
            f.write('\n')

# ---------- 主 ----------
def convert_s2p_to_ri(src: pathlib.Path):
    dst = src.with_name(src.stem + '_RI' + src.suffix)
    with open(src, 'rb') as f:
        freq_hz, data, opt, cmt, unit, z0 = _read_v1(f)
    _write_v1(dst, freq_hz, data, opt, cmt, unit, z0)
    print(f'Converted -> {dst}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python s2p_ri_convert.py  your.s2p'); sys.exit(1)
    src = pathlib.Path(sys.argv[1]).expanduser()
    if not src.is_file():
        print(f'File not found: {src}'); sys.exit(2)
    convert_s2p_to_ri(src)