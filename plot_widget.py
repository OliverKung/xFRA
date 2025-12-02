import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from custom_plot_widget.waveWidget import waveWidget
from xConv.xConv import xConvFormulaTransformer,xConvS2PReader


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    # ---------- 构建 ----------
    def _build_ui(self):
        self.layout = QGridLayout(self)

        self.wave_widget = {}
        self.wave_index = 0

        # 上方：Magnitude
        self.wave_widget['log_1'] = waveWidget(freq_axis='log')
        self.layout.addWidget(self.wave_widget['log_1'], 0, 0)
    

        # 下方：Phase
    # ---------- 添加/删除 wave widget ----------
    def add_wave_widget(self, key, freq_axis='log'):
        self.wave_widget[key] = waveWidget(freq_axis=freq_axis)
        # 优先填充横轴，之后填充纵轴，自动扩充列
        n = self.wave_index
        max = np.floor(np.sqrt(n))
        pos = n - max*max
        if pos < max:
            row = pos
            col = max
        elif pos < 2*max:
            row = max
            col = pos - max
        else:
            row = max
            col = max
        row  = int(row)
        col = int(col)
        self.wave_index += 1
        self.layout.addWidget(self.wave_widget[key], row, col)
    
    def del_wave_widget(self, key):
        if key in self.wave_widget:
            self.layout.removeWidget(self.wave_widget[key])
            self.wave_widget[key].deleteLater()
            del self.wave_widget[key]
    def del_all_wave_widget(self):
        for key in list(self.wave_widget.keys()):
            self.layout.removeWidget(self.wave_widget[key])
            self.wave_widget[key].deleteLater()
            del self.wave_widget[key]
        self.wave_index=0
        
    # ---------- 指定waveWidget添加删除trace ----------
    def add_trace(self, wave_key, name, x_data, y_data,
                  trace_color='#00bfff', unit='', label=''):
        if wave_key in self.wave_widget:
            self.wave_widget[wave_key].add_trace(
                name=name,
                x_data=x_data,
                y_data=y_data,
                trace_color=trace_color,
                unit=unit,
                label=label
            )
    def remove_trace(self, wave_key, name=""):
        if wave_key in self.wave_widget:
            self.wave_widget[wave_key].remove_trace(name)

    def get_wave_widget_list(self):
        return list(self.wave_widget.keys())

    # ---------- 设置指定waveWidget坐标类型 ----------
    def set_freq_axis(self, wave_key, freq_axis: str):
        if wave_key in self.wave_widget:
            self.wave_widget[wave_key].set_freq_axis(freq_axis)


    # ---------- 刷新 ----------
    def replot(self, cfg: dict):
        reader = xConvS2PReader("data\\GRM0115C1C100GE01_DC0V_25degC.s2p")     # 你的文件路径
        s = reader.read()                      # dict: freq, s11, s12, s21, s22, z0

        transformer = xConvFormulaTransformer()
        transformer.load_formulas(s, "xConv\\xConvFormulaDef.json")

        # 2. 计算 S21 实部
        freq = s['freq']                       # Hz
        absCapZ21 = transformer.apply_formula(s,"abs(capZ21)")         # numpy.ndarray
        z21_abs = transformer.apply_formula(s, "imag(z21_config3)")  # 计算阻抗幅值以供参考

        self.set_freq_axis('1', freq_axis='log')
        self.add_trace(wave_key='1',
                       name='S21_real',
                       x_data=freq,
                       y_data=absCapZ21,
                       trace_color='#00bfff',
                       unit='pF',
                       label='Capacitance (pF)')
        self.add_wave_widget('2', freq_axis='lin')
        self.add_trace(wave_key='2',
                       name='Z21_abs',
                       x_data=freq,
                       y_data=z21_abs,
                       trace_color='#ff7f50',
                       unit='Ohm',
                       label='|Z21| (Ohm)')
