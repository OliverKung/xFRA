import json
import os
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets


class waveWidget(QtWidgets.QWidget):
    """
    上下分栏：
      上方：|S21| (dB)
      下方：∠S21 (°)
    光标自动联动，滚轮/拖动已禁用
    """
    cursorMoved = QtCore.Signal(float, dict)   # freq, {trace_name: y_value}

    def __init__(self, parent=None, freq_axis='log'):
        super().__init__(parent)

        self._freq_axis = freq_axis.lower()

        # ---- 构建trace ---- #
        self.traces = {} # name -> trace_info dict
        self.trace_cursor_hLines = {} # name -> trace_cursor_hLines
        self.data = {}   # name -> data array
        self.unit = {}   # name -> unit string
        self.label = {}  # name -> label string

        self.y_min = float('inf')
        self.y_max = float('-inf')
        # ---- 基本状态变量 ---- #
        self.trace_cursor_visible = True
        self.trace_cursor_freeze = False

        # ---- 布局 ----
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)

        # ---- 上方 |S21| ----
        self.pw = pg.PlotWidget()
        self._style_plot(self.pw, 'Frequency (Hz)', 'S21 (dB)')
        self.vLine = pg.InfiniteLine(angle=90, movable=False,
                                         pen=pg.mkPen('#ffeb3b', width=1.2))
        self.pw.addItem(self.vLine)
        self.pw.getViewBox().setMouseEnabled(x=True, y=True)
        # 设置鼠标滚轮事件为重写的wheelEvent方法
        self.pw.wheelEvent = self.wheelEvent
        # self.pw.getViewBox().wheelEvent = lambda ev: pg.ViewBox.wheelEvent(
        #     self.pw.getViewBox(), ev) if ev.modifiers() & (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier) else None

        self.lay.addWidget(self.pw)

        # 光标值标签（右上角）
        self.cursor_label = pg.TextItem(
            anchor=(1, 0), color='#ffeb3b', 
            border=pg.mkPen('#ffeb3b', width=0.5),
            fill=pg.mkBrush(self.style.get('waveWidget', {}).get('label', {}).get('background_color', '#161616'))
        )
        self.pw.addItem(self.cursor_label)

        # ---- 数据 ----
        self.freq = None

        # ---- 鼠标联动 ----
        self.proxy_amp = pg.SignalProxy(self.pw.scene().sigMouseMoved,
                                        rateLimit=60, slot=self._mouse_moved)
        
        # ---- 鼠标双击事件 ----
        self.pw.scene().sigMouseClicked.connect(self._mouse_clicked)

    # ---------------- 鼠标双击事件 ----------------
    def _mouse_clicked(self, evt):
        # 鼠标双击切换光标随动与否
        if evt.double():
            self.trace_cursor_freeze = not self.trace_cursor_freeze


    # ---------------- 重写鼠标滚轮事件，实现按下shift滚轮时缩放x轴，按下ctrl滚轮时缩放y轴，未按下时滚轮仅移动x轴 ----------------
    def wheelEvent(self, ev):
        # 滚轮角度 -> 缩放因子
        delta = ev.angleDelta().y()
        factor = 1.1 if delta < 0 else 1 / 1.1

        # 当前轴范围
        x_range, y_range = self.pw.getViewBox().viewRange()

        if ev.modifiers() & QtCore.Qt.ControlModifier:     # 按住 Ctrl → 仅 Y 轴
            self.pw.getViewBox().setYRange(y_range[0] * factor,
                           y_range[1] * factor,
                           padding=0)
        elif ev.modifiers() & QtCore.Qt.ShiftModifier:     # 按住 Shift → 仅 X 轴
            self.pw.getViewBox().setXRange(x_range[0] * factor,
                           x_range[1] * factor,
                           padding=0)
        else:                                              # 无修饰键 → 默认行为
            super().wheelEvent(ev)

    # ---------------- 工具 ----------------
    def _style_plot(self, pw, xtxt, ytxt):
        style_path = os.path.join(os.path.dirname(__file__), 'style.json')
        try:
            with open(style_path, 'r') as f:
                self.style = json.load(f)
        except Exception as e:
            print(f"Failed to load style.json: {e}")
            self.style = {}

        pw.setBackground(self.style.get('background', self.style.get('waveWidget', {}).get('background', '#222222')))
        for ax in ['bottom', 'left']:
            pw.getAxis(ax).setPen(pg.mkPen(self.style.get('waveWidget', {}).get('axis', {}).get('color', '#999999'), width=self.style.get('waveWidget', {}).get('axis', {}).get('width', 1)))
        pw.showAxis('top', False)
        pw.showAxis('right', False)
        pw.setLabel('bottom', xtxt)
        pw.setLabel('left', ytxt)
        pw.showGrid(x=True, y=True, alpha=self.style.get('waveWidget', {}).get('gridline', {}).get('alpha', 0.3))
        if self._freq_axis == 'log':
            pw.setLogMode(x=True, y=False)
        else:
            pw.setLogMode(x=False, y=False)

    # ---------------- 设置坐标轴题目 ----------------
    def set_axis_labels(self, x_label: str, y_label: str):
        self.pw.setLabel('bottom', x_label)
        self.pw.setLabel('left', y_label)

    # ----------------- 获取迹线名称列表 ----------------
    def get_trace_names(self):
        return list(self.traces.keys())

    # ----------------- 获取当前迹线数量 ----------------
    def get_trace_count(self):
        return len(self.traces)

    # ---------------- 添加迹线 ----------------
    def add_trace(self,name, x_data, y_data, trace_color="#ff8c00",cursor_color='#ffeb3b', unit='dB',label=None):
        """freq: Hz, s21: 复数线性值"""
        self.freq = np.asarray(x_data, dtype=float)
        if self._freq_axis == 'lin':
            self.pw.getViewBox().setLimits(xMin=np.min(self.freq), xMax=np.max(self.freq))
        elif self._freq_axis == 'log':
            self.pw.getViewBox().setLimits(xMin=np.log10(np.min(self.freq)), xMax=np.log10(np.max(self.freq)))
        self.data[name] = np.asarray(y_data, dtype=float)
        self.traces[name]=self.pw.plot(pen=pg.mkPen(trace_color, width=self.style.get('waveWidget', {}).get('trace_width', 5)), name=name)
        self.traces[name].setData(self.freq, self.data[name])
        self.trace_cursor_hLines[name] = pg.InfiniteLine(angle=0, movable=False,
                                            pen=pg.mkPen(cursor_color, width=1.2))
        self.unit[name] = unit
        self.label[name] = label
        # 获取所有数据中数据最大值和最小值，并更新viewBox的y范围限制
        self.y_min = self.y_min if np.min(self.data[name]) > self.y_min else np.min(self.data[name])
        self.y_max = np.max(self.data[name]) if np.max(self.data[name]) > self.y_max else self.y_max
        self.pw.getViewBox().setLimits(yMin=self.y_min - abs(0.1 * (self.y_max-self.y_min)), yMax=self.y_max + abs(0.1 * (self.y_max-self.y_min)))
        
        if unit == "":
            self.set_axis_labels('Frequency (Hz)', name)
        else:
            self.set_axis_labels('Frequency (Hz)', f"{name} ({unit})")

        self.pw.addItem(self.trace_cursor_hLines[name])

        # 默认光标到第一个点
        self._set_cursor(1)
        self.auto_range()
        self.cursor_label_position_update()
    
    # --------------- 删除指定trace ---------------
    def remove_trace(self, name: str=None):
        if name in self.traces:
            self.pw.removeItem(self.traces[name])
            self.pw.removeItem(self.trace_cursor_hLines[name])
            del self.traces[name]
            del self.trace_cursor_hLines[name]
            del self.data[name]
            del self.unit[name]
            del self.label[name]
        #-----不指定名称时，清除所有迹线
        else:
            for trace in self.traces.values():
                self.pw.removeItem(trace)
            for hLine in self.trace_cursor_hLines.values():
                self.pw.removeItem(hLine)
            self.traces.clear()
            self.trace_cursor_hLines.clear()
            self.data.clear()
            self.unit.clear()
            self.label.clear()
        self.auto_range()

    # ---------------- 坐标类型设置 ----------------
    def set_freq_axis(self, freq_axis: str):
        self._freq_axis = freq_axis.lower()
        if self._freq_axis == 'log':
            self.pw.setLogMode(x=True, y=False)
        else:
            self.pw.setLogMode(x=False, y=False)

    # ---------------- 光标私有 ----------------
    def _set_cursor(self, idx):
        if self.freq is None:
            return
        if self._freq_axis == 'log':
            f0 = np.log10(self.freq[idx])
        else:
            f0 = self.freq[idx]
        data = {}
        for name in self.trace_cursor_hLines.keys():
            value = self.data[name][idx]
            self.trace_cursor_hLines[name].setPos(value)
            data[name] = value

        # 上方
        self.vLine.setPos(f0)

        self.cursorMoved.emit(f0, data)

    # ---------------- 鼠标事件 ----------------
    def _mouse_moved(self, evt):
        self._mouse_common(evt[0])

    # ---------------- cursor Label 更新 ----------------
    def cursor_label_update(self, freq, data_dict):
        if freq == 0 or not data_dict:
            self.cursor_label.setText("")
            return
        freq_hz = 10 ** freq
        text = f"\nFreq: {freq_hz/1e6:.3f} MHz\n"
        for name, value in data_dict.items():
            unit = self.unit.get(name, '')
            label = self.label.get(name, name)
            text += f"{label}: {value:.3f} {unit}\n"
        self.cursor_label.setText(text.strip())

    # ---------------- cursor Label 位置更新 ----------------
    def cursor_label_position_update(self):
        view_rect = self.pw.viewRect()
        x_pos = view_rect.right()
        y_pos = view_rect.top()
        self.cursor_label.setPos(view_rect.bottomRight())

    # ---------------- cursor Label 可视化切换 ----------------
    def cursor_label_set_visible(self, visible: bool):
        self.cursor_label.setVisible(visible)

    # ---------------- trace cursor hLine 可视化切换 ----------------
    def trace_cursor_hLine_set_visible(self, name: str=None, visible: bool=True):
        if name is None:
            for hLine in self.trace_cursor_hLines.values():
                hLine.setVisible(visible)
            self.vLine.setVisible(visible)
            self.trace_cursor_visible = visible
            self.cursor_label.setVisible(visible)
            return
        elif name in self.trace_cursor_hLines:
            self.trace_cursor_hLines[name].setVisible(visible)

    # ----------------- 自动缩放 ----------------
    def auto_range(self):
        # ---------------- 获取所有数据的x和y的范围 ----------------
        if not self.data:
            return
        all_y = np.concatenate(list(self.data.values()))
        y_min = np.min(all_y)
        y_max = np.max(all_y)
        x_min = np.min(self.freq)
        x_max = np.max(self.freq)
        # ---------------- 设置视图范围 ----------------
        if self._freq_axis == 'log':
            x_min = np.log10(x_min)
            x_max = np.log10(x_max)
        else:
            pass
        self.pw.setXRange(x_min, x_max, padding=0.02)
        self.pw.setYRange(y_min, y_max, padding=0.1)

    # ----------------- mouse 共同处理 ----------------
    def _mouse_common(self, pos):
        if self.data is None or self.freq is None or len(self.freq) == 0:
            return
        pw = self.pw
        if not pw.sceneBoundingRect().contains(pos):
            return
        mouse_point = pw.plotItem.vb.mapSceneToView(pos)
        x = mouse_point.x()

        # 吸附到最近频率
        if self._freq_axis == 'log':
            idx = int(np.argmin(np.abs(np.log10(self.freq) - x)))
        else:
            idx = int(np.argmin(np.abs(self.freq - x)))
        if not self.trace_cursor_freeze:
            self._set_cursor(idx)
            self.cursor_label_update(np.log10(self.freq[idx]), {name: self.data[name][idx] for name in self.data})
            self.cursor_label_position_update()
        else:
            pass