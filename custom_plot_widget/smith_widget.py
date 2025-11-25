# smith_widget.py
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import skrf as rf

class SmithWidget(pg.PlotWidget):
    cursorMoved = QtCore.Signal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        # ---------------- 视觉基调 ----------------
        self.setBackground('#161616')
        self.getAxis('bottom').setPen(pg.mkPen('#999', width=0.5))
        self.getAxis('left').setPen(pg.mkPen('#999', width=0.5))
        self.showAxis('top', False)
        self.showAxis('right', False)
        self.setAspectLocked(True)
        self.setRange(xRange=(-1.25, 1.25), yRange=(-1.25, 1.25))

        # 栅格 item 置底
        self.grid_items = []
        self._draw_fine_grid()

        # 光标
        self.vLine = pg.InfiniteLine(angle=90, movable=False,
                                     pen=pg.mkPen('#ffeb3b', width=1.2))
        self.hLine = pg.InfiniteLine(angle=0, movable=False,
                                     pen=pg.mkPen('#ffeb3b', width=1.2))
        self.cursor_point = self.plot([0], [0], pen=None,
                                      symbol='o', symbolSize=9,
                                      symbolBrush=None,
                                      symbolPen=pg.mkPen('#ffeb3b', width=2))
        self.addItem(self.vLine)
        self.addItem(self.hLine)
        self.vLine.setZValue(900)
        self.hLine.setZValue(900)
        self.cursor_point.setZValue(1000)

        # 数据
        self.freq = None
        self.gamma = None
        self.proxy = pg.SignalProxy(self.scene().sigMouseMoved,
                                    rateLimit=60, slot=self._mouse_moved)
        vb = self.getViewBox()
        vb.setMouseEnabled(x=False,y=False)
        self.scatter = None

    # ========================================================
    #                    精细栅格
    # ========================================================
    def _draw_fine_grid(self):
        """一次性生成所有栅格路径，避免多次 plot()"""
        # ---------- 等反射系数圆 ----------
        for mag in np.linspace(0.1, 1.0, 5):
            self._add_circle(0, 0, mag,
                             pg.mkPen(pg.mkColor(200, 200, 200, 80 if mag < 1 else 160),
                                      width=1.2 if mag == 2 else 1.2))
            # 填充，仅 |Γ|<1 做轻微透明
            # if mag < 1:
            #     fill = pg.QtWidgets.QGraphicsEllipseItem(-mag, -mag, 2*mag, 2*mag)
            #     fill.setPen(pg.mkPen(None))
            #     fill.setBrush(pg.mkColor(255, 255, 255, 6))
            #     self.addItem(fill)
            #     fill.setZValue(-100)

        # ---------- 等电阻圆 ----------
        for r in [0.2, 0.5, 1.0, 2.0, 5.0]:
            emphasize = (r == 1.0)
            self._add_impedance_circle(r, emphasize)

        # ---------- 等电抗弧 ----------
        for x in [0 ,0.2, 0.5, 1.0, 2.0, 5.0]:
            for sign in [1, -1]:
                emphasize = (abs(x) == 1.0)
                self._add_reactance_arc(x*sign, emphasize)
    # --------------- 工具：加圆 ---------------
    def _add_circle(self, xc, yc, r, pen):
        theta = np.linspace(0, 2*np.pi, 400)
        x = xc + r * np.cos(theta)
        y = yc + r * np.sin(theta)
        item = self.plot(x, y, pen=pen)
        item.setZValue(-50)
        self.grid_items.append(item)

    # --------------- 等阻抗圆 ---------------
    def _add_impedance_circle(self, r, emphasize):
        center = r / (r + 1.0)
        radius = 1.0 / (r + 1.0)
        theta = np.linspace(-np.pi, np.pi, 300)
        x = center + radius * np.cos(theta)
        y = radius * np.sin(theta)
        pen = pg.mkPen(pg.mkColor(100, 200, 255, 180 if emphasize else 120),
                       width=2.0 if emphasize else 1.2)
        item = self.plot(x, y, pen=pen)
        item.setZValue(-40)
        self.grid_items.append(item)

    # --------------- 等电抗弧 ---------------
    def _add_reactance_arc(self, x, emphasize):
        if x == 0:
            xs = [-1,1]
            ys = [0,0]
            pen = pg.mkPen(pg.mkColor(255, 150, 100, 180 if emphasize else 120),
                       width=2.0 if emphasize else 1.2)
            item = self.plot(xs, ys, pen=pen)
            item.setZValue(-40)
            self.grid_items.append(item)
            return
        center_x = 1.0
        radius = 1.0 / abs(x)
        center_y = 1.0 / x
        # 半圆
        if x > 0:
            theta = np.linspace(-np.pi*1/2, -np.pi*3/2, 300)
        else:
            theta = np.linspace(np.pi/2, np.pi*3/2, 300)
        xs = center_x + radius * np.cos(theta)
        ys = center_y + radius * np.sin(theta)
        # 裁剪到单位圆内
        mask = xs**2 + ys**2 <= 1.01
        xs, ys = xs[mask], ys[mask]
        
        pen = pg.mkPen(pg.mkColor(255, 150, 100, 180 if emphasize else 120),
                       width=2.0 if emphasize else 1.2)
        item = self.plot(xs, ys, pen=pen)
        item.setZValue(-40)
        self.grid_items.append(item)

    # ========================================================
    #                      数据 & 光标
    # ========================================================
    def set_data(self, freq, gamma):
        self.freq = np.asarray(freq)
        self.gamma = np.asarray(gamma)
        self._plot()

    # ========================================================
    #                      绘图流程
    # ========================================================

    def _plot(self):
        if self.scatter is not None:
            self.removeItem(self.scatter)
        real = self.gamma.real
        imag = self.gamma.imag
        self.scatter = pg.ScatterPlotItem(
            x=real, y=imag, pen=None,
            brush=pg.mkBrush(0, 255, 255, 180), size=4)
        self.addItem(self.scatter)

    # ========================================================
    #                         光标
    # ========================================================
    def _mouse_moved(self, evt):
        pos = evt[0]
        if not self.sceneBoundingRect().contains(pos):
            return
        mousePoint = self.plotItem.vb.mapSceneToView(pos)
        x, y = mousePoint.x(), mousePoint.y()

        free = (pg.QtGui.QGuiApplication.keyboardModifiers()
                == pg.QtCore.Qt.ControlModifier)

        if self.freq is None or free:
            self.vLine.setPos(x)
            self.hLine.setPos(y)
            self.cursor_point.setData([x], [y])
            self.cursorMoved.emit(0, x, y)
            return

        # 吸附
        dist2 = (self.gamma.real - x)**2 + (self.gamma.imag - y)**2
        idx = int(np.argmin(dist2))
        gr, gi = self.gamma.real[idx], self.gamma.imag[idx]
        self.vLine.setPos(gr)
        self.hLine.setPos(gi)
        self.cursor_point.setData([gr], [gi])
        self.cursorMoved.emit(self.freq[idx], gr, gi)