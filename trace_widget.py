from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel, QSpinBox,
                             QDoubleSpinBox, QComboBox, QPushButton,
                             QGroupBox, QHBoxLayout, QVBoxLayout,
                             QCheckBox, QFrame, QSplitter, QScrollArea)
from PyQt5.QtCore import pyqtSignal, Qt
import math
from basic_custom_widget.QDragGroupBox import DragWidget


class TraceWidget(QWidget):
    # 任何参数改动都发这个信号，dict 携带最新值
    params_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._connect_signals()
        self.data = {}

    # ---------- 构建 ----------
    def _build_ui(self):
        self.setMaximumWidth(520)
        self.setMinimumWidth(470)
        layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        self.dw = DragWidget()
        self.dw.contentChanged.connect(self._notify)
        scroll.setWidget(self.dw)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        self.dw.add_box()
        self._notify()

    # ---------- 信号 ----------
    def _connect_signals(self):
        return

    def _notify(self):
        self.data = self.dw.get_all_content()
        d = {"traces": self.data}
        self.params_changed.emit(d)
    
    def get_trace_params(self):
        self.data=self.dw.get_all_content()
        return self.data