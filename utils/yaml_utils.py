# -*- coding: utf-8 -*-
"""
轻量 YAML 序列化器 — 仅处理简单嵌套结构，无需任何外部依赖。
兼容标准 YAML，生成的文件可直接被 PyYAML 读取，反之亦然。
"""
import re
import numpy as np

__all__ = ["yaml_dump", "yaml_load"]


def _to_plain(obj):
    """将 numpy 类型递归转为 Python 原生类型"""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        return val if not np.isnan(val) and not np.isinf(val) else None
    if isinstance(obj, np.ndarray):
        return [_to_plain(x) for x in obj.tolist()]
    if isinstance(obj, dict):
        return {str(k): _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]
    if isinstance(obj, tuple):
        return [_to_plain(x) for x in obj]
    if isinstance(obj, bool):
        return bool(obj)
    return obj


def _repr_scalar(val):
    """将单个标量转为 YAML 字符串表示"""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        if isinstance(val, float):
            if val != val:
                return ".nan"
            if val == float("inf"):
                return ".inf"
            if val == float("-inf"):
                return "-.inf"
        if isinstance(val, int):
            return repr(val)
        # whole-number float: use repr so "10.0" not "10"
        if val == int(val) and val != float("inf") and val != float("-inf") and val == val:
            return repr(val)
        return f"{val:g}"
    if isinstance(val, str):
        if re.match(r"^[a-zA-Z_][\w\-.,/\\]*$", val) or val == "":
            return val if val else "''"
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(val)


def yaml_dump(data, indent=2):
    """将嵌套 dict/list 序列化为 YAML 字符串"""
    plain = _to_plain(data)
    lines = []
    _dump_lines(plain, lines, indent_level=0, indent=indent)
    return "\n".join(lines) + "\n"


def _dump_lines(obj, lines, indent_level, indent):
    prefix = " " * (indent_level * indent)

    if isinstance(obj, dict):
        for key, val in obj.items():
            k = _repr_scalar(key)
            if isinstance(val, (dict, list)):
                if len(val) == 0:
                    # empty list/dict -> inline
                    lines.append(f"{prefix}{k}: []")
                else:
                    lines.append(f"{prefix}{k}:")
                    _dump_lines(val, lines, indent_level + 1, indent)
            else:
                lines.append(f"{prefix}{k}: {_repr_scalar(val)}")

    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                _dump_lines(item, lines, indent_level + 1, indent)
            else:
                lines.append(f"{prefix}- {_repr_scalar(item)}")

    else:
        lines.append(f"{prefix}{_repr_scalar(obj)}")


# ============================================================
#  YAML Parser — 简单递归下降
# ============================================================

def _indent(line):
    return len(line) - len(line.lstrip(" "))


def yaml_load(text: str):
    lines = text.split("\n")
    idx = [0]
    return _parse_node(lines, idx, -1)


def _is_seq_line(stripped):
    return stripped.startswith("- ") or stripped == "-"


def _parse_node(lines, idx, parent_indent):
    """
    解析一个值。返回值可能是:
    - dict  (映射)
    - list  (序列)
    - 标量   (str/int/float/bool/None)
    - None  (缩进提前结束)
    """
    while idx[0] < len(lines):
        line = lines[idx[0]]
        stripped = line.strip()

        # 跳过空行和注释
        if stripped == "" or stripped.startswith("#"):
            idx[0] += 1
            continue

        cur = _indent(line)

        # 缩进 <= 父级 → 停止
        if parent_indent >= 0 and cur < parent_indent:
            return None

        # ---- 映射 ----
        m = re.match(r"^([^:]+?):\s*(.*)$", stripped)
        if m and not _is_seq_line(stripped):
            key = m.group(1).strip()
            rest = m.group(2).strip()
            idx[0] += 1
            if rest:
                val = _parse_scalar(rest)
            else:
                val = _parse_node(lines, idx, cur)
            more = _parse_mapping(lines, idx, cur)
            more[key] = val
            return more

        # ---- 序列 ----
        if _is_seq_line(stripped):
            return _parse_sequence(lines, idx, cur)

        # ---- 标量 ----
        idx[0] += 1
        return _parse_scalar(stripped)

    return None


def _parse_mapping(lines, idx, parent_indent):
    """收集同层 key: value"""
    result = {}
    while idx[0] < len(lines):
        line = lines[idx[0]]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            idx[0] += 1
            continue
        cur = _indent(line)
        if cur < parent_indent:
            break
        if _is_seq_line(stripped):
            break

        m = re.match(r"^([^:]+?):\s*(.*)$", stripped)
        if m:
            key = m.group(1).strip()
            rest = m.group(2).strip()
            idx[0] += 1
            if rest:
                result[key] = _parse_scalar(rest)
            else:
                result[key] = _parse_node(lines, idx, cur)
        else:
            break
    return result


def _parse_sequence(lines, idx, seq_indent):
    """收集同层 - 项"""
    result = []
    while idx[0] < len(lines):
        line = lines[idx[0]]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            idx[0] += 1
            continue
        cur = _indent(line)
        if cur < seq_indent:
            break

        if stripped.startswith("- "):
            rest = stripped[2:].strip()
            idx[0] += 1
            if rest:
                result.append(_parse_scalar(rest))
            else:
                val = _parse_node(lines, idx, seq_indent)
                if val is not None:
                    result.append(val)
        elif stripped == "-":
            idx[0] += 1
            val = _parse_node(lines, idx, seq_indent)
            if val is not None:
                result.append(val)
        else:
            break
    return result


def _parse_scalar(s):
    s = s.strip()
    if s == "[]":
        return []
    if s == "{}":
        return {}
    if s in ("null", "~", ""):
        return None
    if s in ("true", "True", "yes"):
        return True
    if s in ("false", "False", "no"):
        return False
    if s in (".nan", ".NaN"):
        return float("nan")
    if s == ".inf":
        return float("inf")
    if s == "-.inf":
        return float("-inf")
    try:
        if "." not in s and "e" not in s.lower():
            return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


