from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel, QSpinBox,
                             QDoubleSpinBox, QComboBox, QPushButton,
                             QGroupBox, QHBoxLayout, QVBoxLayout,
                             QCheckBox, QFrame, QSplitter, QScrollArea)
from PyQt5.QtCore import pyqtSignal, Qt
import math
from custom_widget.QDragGroupBox import DragWidget


class TraceWidget(QWidget):
    # 任何参数改动都发这个信号，dict 携带最新值
    params_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._connect_signals()

    # ---------- 构建 ----------
    def _build_ui(self):
        self.setMaximumWidth(520)
        self.setMinimumWidth(470)
        layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        self.dw = DragWidget()
        scroll.setWidget(self.dw)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        self.dw.add_box()

       
    # ---------- 信号 ----------
    def _connect_signals(self):
        print("X")

    def _notify(self):
        d = dict()
        self.params_changed.emit(d)