# io_box.py
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal


class QEngLineEdit(QLineEdit):
    """
    支持 Y(1e24) ~ y(1e-24) 并自动挑选工程单位，
    可拼接用户后缀（如 "V", "Hz"）的 QLineEdit 子类。
    信号：valueChanged(float)
    """
    # 工程单位倍率表
    UNITS = {
        'Y': 1e24, 'Z': 1e21, 'E': 1e18, 'P': 1e15, 'T': 1e12,
        'G': 1e9,  'M': 1e6,  'k': 1e3,  '': 1,
        'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12,
        'f': 1e-15, 'a': 1e-18, 'z': 1e-21, 'y': 1e-24
    }
    DISPLAY_ORDER = ['Y', 'Z', 'E', 'P', 'T', 'G', 'M', 'k', '', 'm', 'u',
                     'n', 'p', 'f', 'a', 'z', 'y']

    valueChanged = pyqtSignal(float)

    def __init__(self, parent=None, alignment=Qt.AlignLeft,
                 sig_figs: int = 10, decimals: int = -1, suffix: str = ""):
        super().__init__(parent)
        self.maxValue = 1e30
        self.minValue = -1e30
        self.setAlignment(alignment)
        self._sig_figs = max(1, sig_figs)
        self._decimals = decimals          # <0 用有效数字
        self._suffix = str(suffix).strip()  # 用户后缀
        self.editingFinished.connect(self._reformat)

    # ----------- 精度控制 ----------
    def set_sig_figs(self, n: int):
        self._sig_figs = max(1, n)
        self._decimals = -1
        self._reformat()

    def sig_figs(self):
        return self._sig_figs

    def set_decimals(self, n: int):
        self._decimals = n
        self._reformat()

    def decimals(self):
        return self._decimals

    # ----------- 对齐 ----------
    def set_alignment(self, alignment):
        self.setAlignment(alignment)

    def alignment(self):
        return super().alignment()

    # ----------- 后缀 ----------
    def setSuffix(self, s: str):
        self._suffix = str(s).strip()
        self._reformat()

    def suffix(self):
        return self._suffix

    # ----------- 数据接口 ----------
    def get_value(self) -> float:
        text = self.text().strip()
        if not text:
            return 0.0
        # 1. 剥后缀
        if self._suffix and text.endswith(self._suffix):
            text = text[:-len(self._suffix)].strip()
        # 2. 剥工程单位
        for unit, scale in self.UNITS.items():
            if text.endswith(unit) and unit !="":
                return float(text[:-1]) * scale
        return float(text) if text else 0.0

    def set_value(self, value: float) -> None:
        if value == 0:
            self.setText("0" + self._suffix)
            self.valueChanged.emit(0.0)
            return
        sign = "-" if value < 0 else ""
        abs_v = abs(value)
        # 自动挑工程单位
        for unit in self.DISPLAY_ORDER:
            scale = self.UNITS.get(unit, 1)
            if abs_v >= scale or unit == 'y':
                num = abs_v / scale
                if self._decimals >= 0:
                    fmt = f"{{:.{self._decimals}f}}"
                else:
                    fmt = f"{{:.{self._sig_figs}g}}"
                text = fmt.format(num).rstrip(".")
                # 拼接：工程单位 + 后缀
                self.setText(sign + text + unit + self._suffix)
                self.valueChanged.emit(float(value))
                return

    # ----------- Qt 风格别名 ----------
    def value(self):
        return self.get_value()

    def setValue(self, v):
        self.set_value(v)

    def is_empty(self):
        return self.text().strip() == ""

    def clear(self):
        super().clear()
        self.valueChanged.emit(0.0)

    # ----------- 内部 ----------
    def _reformat(self):
        try:
            v = self.get_value()
            if v < self.minValue:
                v = self.minValue
            elif v > self.maxValue:
                v = self.maxValue
            self.set_value(v)
        except ValueError:
            pass
    # ----------- 限制 ----------
    def setLimits(self, min_value: float, max_value: float):
        self.minValue = min_value
        self.maxValue = max_value