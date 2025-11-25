import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._view_mag = None
        self._view_pha = None
        self._curve_mag = None
        self._curve_pha = None
        self._build_ui()

    # ---------- 构建 ----------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 上方：Magnitude
        self.plot_mag = pg.PlotWidget(title="Magnitude")
        self.plot_mag.setLabel('left', 'Magnitude', 'dB')
        self.plot_mag.setLabel('bottom', 'Frequency', 'Hz')
        self.plot_mag.setLogMode(x=True)
        self.plot_mag.showGrid(x=True, y=True, alpha=0.3)
        self.plot_mag.addLine(x=None, y=0, pen=pg.mkPen('w', width=1, style=Qt.DashLine))
        self._curve_mag = self.plot_mag.plot(pen='cyan')

        # 下方：Phase
        self.plot_pha = pg.PlotWidget(title="Phase")
        self.plot_pha.setLabel('left', 'Phase', '°')
        self.plot_pha.setLabel('bottom', 'Frequency', 'Hz')
        self.plot_pha.setLogMode(x=True)
        self.plot_pha.showGrid(x=True, y=True, alpha=0.3)
        self.plot_pha.setYRange(-200, 200)
        self._curve_pha = self.plot_pha.plot(pen='yellow')

        layout.addWidget(self.plot_mag, stretch=2)
        layout.addWidget(self.plot_pha, stretch=1)

    # ---------- 刷新 ----------
    def replot(self, cfg: dict):
        fstart = cfg['fstart']
        fstop = cfg['fstop']
        points = cfg['points']
        f = np.logspace(np.log10(fstart), np.log10(fstop), points)

        # 随便造一个二阶低通相位
        fc = 15e3
        mag = 20 * np.log10(1 / np.sqrt(1 + (f / fc) ** 4))
        phase = -np.arctan(f / fc) * 2 * 180 / np.pi

        self._curve_mag.setData(f, mag)
        self._curve_pha.setData(f, phase)