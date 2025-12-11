#!/usr/bin/env python3
import argparse
import importlib
import sys
from pathlib import Path

# -------------------- 参数解析 --------------------
parser = argparse.ArgumentParser(description="动态加载测量/激励设备类")
parser.add_argument('--m-device-model', required=True,
                    help='测量设备型号，对应 Measurement/<型号>.py 中的类名')
parser.add_argument('--e-device-model', required=True,
                    help='激励设备型号，对应 Excitation/<型号>.py 中的类名')
args = parser.parse_args()

m_model = args.m_device_model
e_model = args.e_device_model

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

# -------------------- 主流程 --------------------
Meas = load_device_class("Measurement", m_model)   # 测量类
Exct = load_device_class("Excitation", e_model)    # 激励类

# 演示：实例化并打印
meas_inst = Meas()
exct_inst = Exct()
print("测量设备实例:", meas_inst)
print("激励设备实例:", exct_inst)