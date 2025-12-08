# -*- coding: utf-8 -*-
"""
完整可运行：Trace 管理器
- 标题栏 + handle 均可拖拽
- 仅标题栏背景变色
- 松手自动居中 + 淡入动画
"""
import sys, json
from PyQt5.QtCore import (Qt, QMimeData, pyqtSignal, QPropertyAnimation,
                          QPoint, QTimer)
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QGroupBox,
                             QHBoxLayout, QLineEdit, QSpinBox, QCheckBox,
                             QPushButton, QScrollArea, QLabel)
from PyQt5.QtGui import QDrag, QPainter
from trace_config import TraceConfigWidget

# --------------------------------------------------
# 1. 业务子控件：Trace X + 标题栏变色 + 双拖拽触发
# --------------------------------------------------
class trace_config_GroupBox(QGroupBox):
    params_changed = pyqtSignal(dict)
    COLOR_TABLE = ["#ef5350", "#ab47bc", "#5c6bc0",
                   "#29b6f6", "#66bb6a", "#ffa726"]

    def __init__(self,index:int, parent=None):
        super().__init__(parent)
        self.trace_id = index
        self.setTitle(f'Trace {self.trace_id}')

        # 仅标题栏背景色
        self.color = self.COLOR_TABLE[(self.trace_id - 1) % len(self.COLOR_TABLE)]
        color = self.color
        self.setStyleSheet(f"""
        trace_config_GroupBox::title {{
            background-color: {color};
            color: white;
            border-radius: 3px;
            padding: 4px 6px;
        }}
        trace_config_GroupBox {{
            border: 1px solid {color};
            border-radius: 4px;
            margin-top: 4px;
        }}
        """)

        # 内部控件
        self.trace_config = TraceConfigWidget()
        self.trace_config.trace_config_changed.connect(self.on_inner_changed)
        self.btn_del = QPushButton('del')
        self.btn_del.clicked.connect(self._ask_delete)

        # 拖拽 handle
        self.handle = QLabel("⋮⋮")
        self.handle.setCursor(Qt.OpenHandCursor)

        lay = QVBoxLayout()
        lay.addWidget(self.trace_config)
        lay.addWidget(self.btn_del)

        container = QWidget()
        container.setLayout(lay)
        outer = QVBoxLayout(self)
        outer.addWidget(container)

        self.param = {}

        self.setMaximumHeight(420)
        self._drag_start_pos = None

    # ---------- 双区域启动拖拽：标题栏 或 handle ------
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            src = self.childAt(ev.pos())
            # handle 或标题栏（y<30）
            if src is self.handle or ev.pos().y() < 30:
                self._drag_start_pos = ev.pos()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if (not (ev.buttons() & Qt.LeftButton) or
            self._drag_start_pos is None or
            (ev.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance()):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData('application/x-box', b'')
        drag.setMimeData(mime)
        drag.exec_(Qt.MoveAction)
        self._drag_start_pos = None

    # ---------- 内容 / 删除 / 动画 -----------------
    def get_content(self):
        self.param=self.trace_config.get_config()
        self.param['color']=self.color
        self.param['trace_id']=self.trace_id
        return self.param

    def on_inner_changed(self, params: dict):
        self.param=params
        self.params_changed.emit(self.param)

    def _ask_delete(self):
        pw = self.parent()
        if pw and hasattr(pw, 'remove_box'):
            pw.remove_box(self)

    # 淡入+缩放动画（120 ms）
    def animate_insert(self):
        self.setWindowOpacity(0.0)
        self._scale = 0.95
        self.update()

        def set_scale(v): self._scale = v; self.update()
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(120)
        fade.setStartValue(0.0), fade.setEndValue(1.0)
        scale = QPropertyAnimation(self, b"_scale")
        scale.setDuration(120)
        scale.setStartValue(0.95), scale.setEndValue(1.0)
        scale.valueChanged.connect(set_scale)
        fade.start(), scale.start()

    _scale = 1.0

    def paintEvent(self, ev):
        p = QPainter(self)
        p.scale(self._scale, self._scale)
        super().paintEvent(ev)


# --------------------------------------------------
# 2. 容器：增删、拖拽排序、自动居中、统一信号
# --------------------------------------------------
class DragWaveWidget(QWidget):
    contentChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = QVBoxLayout(self)
        self._lay.setSpacing(6)
        self._lay.addStretch()
        # self.btn_add = QPushButton('Add Trace')
        # self.btn_add.clicked.connect(self.add_box)
        # self._lay.insertWidget(0, self.btn_add)
        self.setAcceptDrops(True)
        self.trace_boxes = {}
        self._total_traces = 0

    # ---------- 增 / 删 ------------------------------
    def add_box(self,box_type = "trace"):
        print(box_type)
        self._total_traces += 1
        print(f"Adding box {self._total_traces} of type {box_type}")
        if box_type == "trace":
            self.trace_boxes[self._total_traces] = trace_config_GroupBox(self._total_traces)
            print(f"Created trace_config_GroupBox with ID {self._total_traces}")
        elif box_type == "expression":
            self.trace_boxes[self._total_traces] = trace_config_GroupBox(self._total_traces)
            self.trace_boxes[self._total_traces].trace_config.lcb_meas.setCurrentText("Expr")
            print(f"Created expression_config_GroupBox with ID {self._total_traces}")
        else:
            print(f"Unknown box type: {box_type}")
            return
        box = self.trace_boxes[self._total_traces]
        # box.params_changed.connect(self._collect_and_emit)
        self._lay.insertWidget(self._lay.count() - 1, box)
        QTimer.singleShot(60, lambda: self._scroll_to_box(box))

    def remove_box(self, box):
        self._lay.removeWidget(box)
        self.trace_boxes.pop(box.trace_id, None)
        box.deleted = True
        box.deleteLater()
        self._collect_and_emit()

    # ---------- 拖拽：实时插入 ----------------------
    def dragEnterEvent(self, ev):
        if ev.mimeData().hasFormat('application/x-box'):
            ev.acceptProposedAction()

    def dragMoveEvent(self, ev):
        if not ev.mimeData().hasFormat('application/x-box'):
            return
        pos = ev.pos()
        widget = self.childAt(pos)
        if not widget:
            return
        while widget and not isinstance(widget, trace_config_GroupBox):
            widget = widget.parentWidget()
        if not widget:
            return
        src = ev.source()
        src_idx = self._lay.indexOf(src)
        dst_idx = self._lay.indexOf(widget)
        if src_idx != dst_idx:
            self._lay.insertWidget(dst_idx, src)
        ev.acceptProposedAction()

    def dropEvent(self, ev):
        ev.acceptProposedAction()
        QTimer.singleShot(50, lambda: self._scroll_to_box(ev.source()))

    def _scroll_to_box(self, box):
        scroll = self.parentWidget()
        while scroll and not isinstance(scroll, QScrollArea):
            scroll = scroll.parentWidget()
        if scroll:
            scroll.ensureWidgetVisible(box, yMargin=80)

    # ---------- 统一采集 -----------------------------
    def _collect_and_emit(self):
        data = {}
        for idx, box in self.trace_boxes.items():
            data[idx] = box.get_content()
            data[idx]['trace_id'] = idx
        self.contentChanged.emit(data)
    # ---------- 采集不发送信号 ----------------------
    def get_all_content(self):
        data={}
        for idx, box in self.trace_boxes.items():
            # 如果返回空字典，则说明已被删除，跳过
            if box.get_content() == {}:
                continue
            data[idx] = box.get_content()
        return data


# --------------------------------------------------
# 3. 演示窗口
# --------------------------------------------------
class Demo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyQt Trace 双拖拽触发+标题栏变色 完整示例')
        self.resize(700, 450)
        scroll = QScrollArea(self)
        self.dw = DragWaveWidget()
        scroll.setWidget(self.dw)
        scroll.setWidgetResizable(True)
        main = QVBoxLayout(self)
        main.addWidget(scroll)
        self.dw.contentChanged.connect(
            lambda d: print(json.dumps(d, ensure_ascii=False, indent=2)))
        # 初始两个
        self.dw.add_box()
        self.dw.add_box()


# --------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    sys.exit(app.exec_())