#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带光标/吸附/频率显示的史密斯圆图
author : github.com/letusgit
"""
import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                               QPushButton, QFileDialog, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt
import skrf as rf
from smith_widget import SmithWidget
from s21_widget import S21Widget

# -------------------------------------------------
#  主窗口
# -------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xFRA")
        self.resize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)

        # 顶部按钮
        hbox = QHBoxLayout()
        self.btnOpen = QPushButton("打开 s2p 文件")
        self.btnOpen.clicked.connect(self.load_s2p)
        hbox.addWidget(self.btnOpen)
        hbox.addStretch()
        self.label_info = QLabel("请先选择一个二端口 s2p 文件")
        hbox.addWidget(self.label_info)
        lay.addLayout(hbox)

        # 史密斯图
        self.smith = SmithWidget()
        lay.addWidget(self.smith)
        self.S21 = S21Widget()
        lay.addWidget(self.S21)
        # 状态栏
        self.statusBar().showMessage("就绪")
        self.smith.cursorMoved.connect(self._update_status)

        # 数据
        self.freq = None
        self.gamma = None
        self.scatter = None
        self.z0 = 50.0

    # ---------- 打开 ----------
    def load_s2p(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选取 Touchstone 文件", "", "Touchstone (*.s2p)")
        if not path:
            return
        try:
            ntwk = rf.Network(path)          # skrf 读取
            # 取出复数 S11/S21，形状 (n_freq,)
            self.freq   = ntwk.f              # Hz
            self.s11    = ntwk.s[:, 0, 0]     # 复数 ndarray
            self.s21    = ntwk.s[:, 1, 0]     # 复数 ndarray
            self.z0     = ntwk.z0[0, 0].real if ntwk.z0.size > 1 else 50.0

            # 向下分发数据
            self.smith.set_data(self.freq, self.s11)   # Smith 圆图
            self.S21.set_data(self.freq, self.s21)  # 幅相图

            self.label_info.setText(f"已加载：{path}   点数：{len(self.freq)}")
        except Exception as e:
            print(e)
            self.label_info.setText(f"加载失败：{e}")

    # def load_s2p(self):
    #     path, _ = QFileDialog.getOpenFileName(
    #         self, "选取 Touchstone 文件", "", "Touchstone (*.s2p)")
    #     if not path:
    #         return
    #     try:
    #         ntwk = rf.Network(path)
    #         self.freq = ntwk.f
    #         self.gamma = ntwk.s[:, 0, 0]
    #         print(self.gamma)
    #         self.z0 = ntwk.z0[0, 0].real if ntwk.z0.size > 1 else 50.0
    #         self.smith.set_data(self.freq, self.gamma)
    #         self._plot()
    #         self.label_info.setText(f"已加载：{path}   点数：{len(self.freq)}")
    #     except Exception as e:
    #         self.label_info.setText(f"加载失败：{e}")

    # ---------- 画图 ----------
    # def _plot(self):
    #     if self.scatter is not None:
    #         self.smith.removeItem(self.scatter)
    #     real = self.gamma.real
    #     imag = self.gamma.imag
    #     self.scatter = pg.ScatterPlotItem(
    #         x=real, y=imag, pen=None,
    #         brush=pg.mkBrush(0, 255, 255, 180), size=4)
    #     self.smith.addItem(self.scatter)

    # ---------- 状态栏 ----------
    def _update_status(self, f, gr, gi):
        if f == 0:               # 自由模式
            self.statusBar().showMessage(
                f"自由光标  Γ = {gr:.3f} + j{gi:.3f}")
            return
        gamma = complex(gr, gi)
        mag = abs(gamma)
        phase = np.angle(gamma, deg=True)
        z = self.z0 * (1 + gamma) / (1 - gamma)
        self.statusBar().showMessage(
            f"频率 {f/1e9:.3f} GHz  |  Γ = {mag:.3f} ∠{phase:.1f}°  |  Z = {z.real:.1f} + j{z.imag:.1f} Ω")


# ----------------- main -----------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    pg.setConfigOptions(antialias=True)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())