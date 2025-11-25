# s21_widget.py
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets


class S21Widget(QtWidgets.QWidget):
    """
    上下分栏：
      上方：|S21| (dB)
      下方：∠S21 (°)
    光标自动联动，滚轮/拖动已禁用
    """
    cursorMoved = QtCore.Signal(float, float, float)   # freq, s21_db, s21_phase

    def __init__(self, parent=None, freq_axis='log'):
        super().__init__(parent)

        self._freq_axis = freq_axis.lower()

        # ---- 布局 ----
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)

        # ---- 上方 |S21| ----
        self.pw_amp = pg.PlotWidget()
        self._style_plot(self.pw_amp, 'Frequency (Hz)', 'S21 (dB)')
        self.curve_amp = self.pw_amp.plot(pen=pg.mkPen('#00d2ff', width=1.8))
        self.vLine_amp = pg.InfiniteLine(angle=90, movable=False,
                                         pen=pg.mkPen('#ffeb3b', width=1.2))
        self.hLine_amp = pg.InfiniteLine(angle=0, movable=False,
                                         pen=pg.mkPen('#ffeb3b', width=1.2))
        self.pw_amp.addItem(self.vLine_amp)
        self.pw_amp.addItem(self.hLine_amp)
        self.pw_amp.getViewBox().setMouseEnabled(x=True, y=False)

        # ---- 下方 ∠S21 ----
        self.pw_pha = pg.PlotWidget()
        self._style_plot(self.pw_pha, 'Frequency (Hz)', '∠S21 (°)')
        self.curve_pha = self.pw_pha.plot(pen=pg.mkPen('#ff8c00', width=1.8))
        self.vLine_pha = pg.InfiniteLine(angle=90, movable=False,
                                         pen=pg.mkPen('#ffeb3b', width=1.2))
        self.hLine_pha = pg.InfiniteLine(angle=0, movable=False,
                                         pen=pg.mkPen('#ffeb3b', width=1.2))
        self.pw_pha.addItem(self.vLine_pha)
        self.pw_pha.addItem(self.hLine_pha)
        self.pw_pha.getViewBox().setMouseEnabled(x=True, y=False)
        # 固定 Y 范围
        self.pw_pha.setYRange(-180, 180)

        self.lay.addWidget(self.pw_amp)
        self.lay.addWidget(self.pw_pha)

        # ---- 数据 ----
        self.freq = None
        self.s21 = None

        # ---- 鼠标联动 ----
        self.proxy_amp = pg.SignalProxy(self.pw_amp.scene().sigMouseMoved,
                                        rateLimit=60, slot=self._mouse_moved_amp)
        self.proxy_pha = pg.SignalProxy(self.pw_pha.scene().sigMouseMoved,
                                        rateLimit=60, slot=self._mouse_moved_pha)

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
    def set_data(self, freq, s21):
        """freq: Hz, s21: 复数线性值"""
        self.freq = np.asarray(freq, dtype=float)
        self.s21 = np.asarray(s21, dtype=complex)

        s21_db = 20 * np.log10(np.abs(self.s21) + 1e-12)
        s21_phase = np.angle(self.s21, deg=True)

        self.curve_amp.setData(self.freq, s21_db)
        self.curve_pha.setData(self.freq, s21_phase)

        # 默认光标到第一个点
        self._set_cursor(1)

    # ---------------- 光标私有 ----------------
    def _set_cursor(self, idx):
        if self.freq is None:
            return
        f0 = np.log10(self.freq[idx])
        s21_db = 20 * np.log10(np.abs(self.s21[idx]) + 1e-12)
        
        s21_pha = np.angle(self.s21[idx], deg=True)
        # 上方
        self.vLine_amp.setPos(f0)
        self.hLine_amp.setPos(s21_db)
        # 下方
        self.vLine_pha.setPos(f0)
        self.hLine_pha.setPos(s21_pha)

        self.cursorMoved.emit(f0, s21_db, s21_pha)

    # ---------------- 鼠标事件 ----------------
    def _mouse_moved_amp(self, evt):
        self._mouse_common(evt[0], source='amp')

    def _mouse_moved_pha(self, evt):
        self._mouse_common(evt[0], source='pha')

    def _mouse_common(self, pos, source):
        pw = self.pw_amp if source == 'amp' else self.pw_pha
        if not pw.sceneBoundingRect().contains(pos):
            return
        mouse_point = pw.plotItem.vb.mapSceneToView(pos)
        x = mouse_point.x()

        # Ctrl 按下 = 自由模式
        free = (pg.QtGui.QGuiApplication.keyboardModifiers()
                == QtCore.Qt.ControlModifier)

        if self.freq is None or free:
            # 自由十字线
            self.vLine_amp.setPos(x)
            self.vLine_pha.setPos(x)
            y_amp = mouse_point.y() if source == 'amp' else self.hLine_amp.value()
            y_pha = mouse_point.y() if source == 'pha' else self.hLine_pha.value()
            self.hLine_amp.setPos(y_amp)
            self.hLine_pha.setPos(y_pha)
            self.cursorMoved.emit(x, y_amp, y_pha)
            return

        # 吸附到最近频率
        if self._freq_axis == 'log':
            idx = int(np.argmin(np.abs(np.log10(self.freq) - x)))
        else:
            idx = int(np.argmin(np.abs(self.freq - x)))
        self._set_cursor(idx)