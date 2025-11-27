import numpy as np
import re
import cmath
from typing import Dict, Tuple, List, Any
import warnings
import json
import os

class xConvS2PReader:
    """读取Touchstone s2p文件并提取S参数"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.freq = None  # 频率数组 (Hz)
        self.s11 = None   # S11复数数组
        self.s12 = None   # S12复数数组
        self.s21 = None   # S21复数数组
        self.s22 = None   # S22复数数组
        self.z0 = 50.0    # 参考阻抗
        self.freq_unit = None  # 频率单位
        
    def read(self) -> Dict[str, Any]:
        """
        读取s2p文件并返回S参数字典
        返回: {'freq': array, 's11': array, 's12': array, 's21': array, 's22': array, 'z0': float}
        """
        with open(self.file_path, 'r') as f:
            lines = f.readlines()
        
        # 解析选项行和数据
        data_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('!'):
                continue
            if line.startswith('#'):
                self._parse_option_line(line)
            else:
                data_lines.append(line)
        
        # 解析数据
        self._parse_data(data_lines)
        
        return {
            'freq': self.freq,
            's11': self.s11,
            's12': self.s12,
            's21': self.s21,
            's22': self.s22,
            'z0': self.z0
        }
    
    def _parse_option_line(self, line: str):
        """解析选项行，如: # HZ S RI R 50"""
        parts = line[1:].strip().upper().split()
        if len(parts) >= 4:
            self.freq_unit = parts[0]  # HZ, KHZ, MHZ, GHZ
            # 参数类型: S, Y, Z等
            # 格式: RI (实部/虚部), MA (幅度/相位), DB (dB/相位)
            format_type = parts[2]
            if 'R' in parts:
                r_idx = parts.index('R')
                if r_idx + 1 < len(parts):
                    self.z0 = float(parts[r_idx + 1])
    
    def _parse_data(self, data_lines: List[str]):
        """解析S参数数据行"""
        freq = []
        s11, s12, s21, s22 = [], [], [], []
        
        for line in data_lines:
            values = [float(x) for x in line.split()]
            if len(values) >= 9:  # 频率 + 8个S参数值
                freq.append(values[0])
                # 解析为复数 (实部, 虚部格式)
                s11.append(complex(values[1], values[2]))
                s12.append(complex(values[3], values[4]))
                s21.append(complex(values[5], values[6]))
                s22.append(complex(values[7], values[8]))
        
        # 频率单位转换到Hz
        freq = np.array(freq)
        unit_multiplier = {
            'HZ': 1,
            'KHZ': 1e3,
            'MHZ': 1e6,
            'GHZ': 1e9
        }
        if self.freq_unit in unit_multiplier:
            freq *= unit_multiplier[self.freq_unit]
        
        self.freq = freq
        self.s11 = np.array(s11)
        self.s12 = np.array(s12)
        self.s21 = np.array(s21)
        self.s22 = np.array(s22)


class xConvFormulaTransformer:
    """安全地解析和应用文本公式，支持动态注册中间变量"""

    # 原有 SAFE_MATH 保持不变
    SAFE_MATH = {
        'abs': abs,
        'complex': complex,
        'pow': pow,
        'round': round,
        'divmod': divmod,
        'max': max,
        'min': min,
        'sqrt': np.sqrt,
        'exp': np.exp,
        'log': np.log,
        'log10': np.log10,
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'asin': np.arcsin,
        'acos': np.arccos,
        'atan': np.arctan,
        'atan2': np.arctan2,
        'sinh': np.sinh,
        'cosh': np.cosh,
        'tanh': np.tanh,
        'degrees': np.degrees,
        'radians': np.radians,
        'phase': np.angle,
        'unwrap': np.unwrap,
        'real': np.real,
        'imag': np.imag,
        'conj': np.conj,
        'angle': np.angle,
        'mag': np.abs,
        'db': lambda x: 20 * np.log10(np.maximum(np.abs(x), 1e-15)),
        'pi': np.pi,
        'e': np.e,
        'j': 1j,
    }

    def __init__(self):
        self.variables = {}  #  新增：用户注册的中间变量
        self._formula = {} # 公式来源记录

    # 新增：注册中间变量
    def register(self, name: str, formula: str, s_params: dict):
        """注册一个中间变量，供后续公式使用"""
        value = self.apply_formula(s_params, formula)
        self.variables[name] = value
        self._formula[name] = formula  # 记录公式来源
        print(f"已注册变量: {name}")

    # 新增：列出变量
    def list_variables(self):
        print("当前已注册变量:")
        for name in self.variables:
            print(f"  {name}")

    # 新增：清除变量
    def clear_variables(self):
        self.variables.clear()
        print("已清除所有用户变量")

    # 修改：apply_formula 现在支持使用已注册变量
    def apply_formula(self, s_params: dict, formula: str) -> np.ndarray:
        namespace = self.create_safe_namespace(s_params)
        namespace.update(self.variables)  # 加入用户变量

        try:
            result = eval(formula, {"__builtins__": {}}, namespace)
            if isinstance(result, (int, float, complex, np.number)):
                return np.full_like(s_params['freq'], result, dtype=complex)
            elif isinstance(result, (list, tuple)):
                return np.array(result, dtype=complex)
            return result
        except Exception as e:
            raise ValueError(f"公式解析错误 '{formula}': {str(e)}")

    # 原有方法不变，仅内部调用
    @staticmethod
    def create_safe_namespace(s_params: dict) -> dict:
        namespace = {**xConvFormulaTransformer.SAFE_MATH}
        for key, value in s_params.items():
            if isinstance(value, np.ndarray):
                namespace[key] = value
        namespace['array'] = np.array
        namespace['where'] = np.where
        namespace['ones_like'] = np.ones_like
        namespace['zeros_like'] = np.zeros_like
        return namespace

    #  原有方法不变
    @staticmethod
    def validate_formula(formula: str) -> Tuple[bool, str]:
        try:
            compiled = compile(formula, '<string>', 'eval')
            import ast
            tree = ast.parse(formula, mode='eval')
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    return False, f"不允许属性访问: {ast.unparse(node)}"
                elif isinstance(node, ast.Name) and node.id.startswith('__'):
                    return False, f"不允许的属性名: {node.id}"
            return True, ""
        except SyntaxError as e:
            return False, f"语法错误: {str(e)}"
    # ----------- 1. 保存公式定义 -----------
    def save_formulas(self, path: str = "xConv\\xConvFormulaDef.json"):
        """把当前用户变量的【公式】保存为 json 文件（不含计算结果）"""
        # 只保存 name:formula 映射
        formula_dict = {name: self._formula.get(name, "") for name in self.variables}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(formula_dict, f, indent=2, ensure_ascii=False)
        print(f"公式定义已保存到 {path}")

    # ----------- 2. 加载公式定义 -----------
    def load_formulas(self, s_params: dict, path: str = "xConv\\xConvFormulaDef.json"):
        """从 json 文件读取公式并重新注册（需提供 s_params）"""
        if not os.path.isfile(path):
            print(f"文件不存在，跳过加载: {path}")
            return
        with open(path, "r", encoding="utf-8") as f:
            formula_dict = json.load(f)
        # 先清空旧变量
        self.variables.clear()
        self._formula = {}          # 新增：记录公式源码
        for name, formula in formula_dict.items():
            self.register(name, formula, s_params)
        print(f"公式定义已加载自 {path}")


# 使用示例
def main():
    # 1. 读取s2p文件（完全不变）
    reader = xConvS2PReader("data\\GRM0115C1C100GE01_DC0V_25degC.s2p")
    s_params = reader.read()

    # 2. 创建转换器（完全不变）
    transformer = xConvFormulaTransformer()
    transformer.load_formulas(s_params, "xConv\\xConvFormulaDef.json")

    # 3. ✅ 新增：注册中间变量
    # transformer.register("omega", "2*pi*freq", s_params)
    # transformer.register("s21_db", "db(s21)", s_params)

    # 4. ✅ 新增：使用中间变量构建复杂公式
    result = transformer.apply_formula(s_params, "capZ21")
    print(f"复杂公式前五个点: {result[:5]}")
    # transformer.save_formulas("xConv\\xConvFormulaDef.json")
    # 5. ✅ 新增：查看变量
    transformer.list_variables()

    # 6. ✅ 新增：清除变量
    transformer.clear_variables()



def unwrap(phase):
    """相位解卷绕"""
    return np.unwrap(phase)


if __name__ == "__main__":
    main()