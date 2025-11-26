# s21_widget.py
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
        self.hLines = {} # name -> hLine
        self.data = {}   # name -> data array
        self.unit = {}   # name -> unit string
        self.label = {}  # name -> label string

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
        self.pw.getViewBox().setMouseEnabled(x=True, y=False)

        self.lay.addWidget(self.pw)

        # 光标值标签（右上角）
        self.cursor_label = pg.TextItem(
            anchor=(1, 0), color='#ffeb3b', 
            border=pg.mkPen('#ffeb3b', width=0.5),
            fill=pg.mkBrush('#161616')
        )
        self.pw.addItem(self.cursor_label)

        # ---- 数据 ----
        self.freq = None
        self.s21 = None

        # ---- 鼠标联动 ----
        self.proxy_amp = pg.SignalProxy(self.pw.scene().sigMouseMoved,
                                        rateLimit=60, slot=self._mouse_moved)

    # ---------------- 工具 ----------------
    def _style_plot(self, pw, xtxt, ytxt):
        pw.setBackground('#161616')
        for ax in ['bottom', 'left']:
            pw.getAxis(ax).setPen(pg.mkPen('#999', width=0.5))
        pw.showAxis('top', False)
        pw.showAxis('right', False)
        pw.setLabel('bottom', xtxt)
        pw.setLabel('left', ytxt)
        pw.showGrid(x=True, y=True, alpha=60)
        if self._freq_axis == 'log':
            pw.setLogMode(x=True, y=False)
        else:
            pw.setLogMode(x=False, y=False)

    # ---------------- 数据入口 ----------------
    def add_trace(self,name, x_data, y_data, trace_color="#ff8c00",cursor_color='#ffeb3b', unit='dB',label=None):
        """freq: Hz, s21: 复数线性值"""
        self.freq = np.asarray(x_data, dtype=float)
        self.data[name] = np.asarray(y_data, dtype=float)
        self.traces[name]=self.pw.plot(pen=pg.mkPen(trace_color, width=1.8), name=name)
        self.traces[name].setData(self.freq, self.data[name])
        self.hLines[name] = pg.InfiniteLine(angle=0, movable=False,
                                            pen=pg.mkPen(cursor_color, width=1.2))
        self.unit[name] = unit
        self.label[name] = label
        
        self.pw.addItem(self.hLines[name])

        # 默认光标到第一个点
        self._set_cursor(1)

    # ---------------- 光标私有 ----------------
    def _set_cursor(self, idx):
        if self.freq is None:
            return
        f0 = np.log10(self.freq[idx])
        data = {}
        for name in self.hLines.keys():
            value = self.data[name][idx]
            self.hLines[name].setPos(value)
            data[name] = value

        # 上方
        self.vLine.setPos(f0)

        self.cursorMoved.emit(f0, data)

    # ---------------- 鼠标事件 ----------------
    def _mouse_moved(self, evt):
        self._mouse_common(evt[0])

    def _mouse_common(self, pos):
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
        self._set_cursor(idx)