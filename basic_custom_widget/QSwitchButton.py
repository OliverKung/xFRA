# switch_button.py
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint, QEasingCurve, QVariantAnimation
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen


class QSwitchButton(QWidget):
    """直角矩形开关按钮"""
    toggled = pyqtSignal(bool)

    def __init__(self,
                 parent=None,
                 width=46,
                 height=26,
                 bg_off="#D8D8D8",
                 bg_on="#4096FF",
                 slider_color="#ffffff",
                 animation_duration=200):
        super().__init__(parent)

        self._w = width
        self._h = height
        self._bg_off = QColor(bg_off)
        self._bg_on = QColor(bg_on)
        self._slider_color = QColor(slider_color)

        self._margin = 3                 # 滑块距边框间隙
        self._slider_width = height - 2 * self._margin
        self._on = False
        self._slider_x = self._margin    # 滑块当前 x 坐标（动画过程会变化）

        # 动画对象
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(animation_duration)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_value_changed)

        self.setFixedSize(QSize(width, height))
        self.setCursor(Qt.PointingHandCursor)

    # ------------------ 公共接口 ------------------
    def isOn(self):
        return self._on

    def setOn(self, on: bool, animate=True):
        if self._on == on:
            return
        self._on = on
        self._start_anim(animate)
        self.toggled.emit(self._on)

    def toggle(self):
        self.setOn(not self._on)

    # ------------------ 内部 ------------------
    def _start_anim(self, animate):
        start = self._slider_x
        end = self._margin if not self._on else self._w - self._slider_width - self._margin
        if animate:
            self._anim.setStartValue(start)
            self._anim.setEndValue(end)
            self._anim.start()
        else:
            self._slider_x = end
            self.update()

    def _on_value_changed(self, v):
        self._slider_x = v
        self.update()

    # ------------------ 事件 ------------------
    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.toggle()
        super().mouseReleaseEvent(ev)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)  # 直角矩形，不需要抗锯齿

        # 画背景
        bg_brush = QBrush(self._bg_on if self._on else self._bg_off)
        p.fillRect(self.rect(), bg_brush)

        # 画滑块
        slider_rect = QRect(QPoint(int(self._slider_x), self._margin),
                            QSize(self._slider_width, self._slider_width))
        p.fillRect(slider_rect, QBrush(self._slider_color))

        # 画边框（可选）
        p.setPen(QPen(QColor("#999999"), 1))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


# ------------------ 简单演示 ------------------
if __name__ == '__main__':
    app = QApplication([])
    app.setStyleSheet("QWidget{font-family:微软雅黑;font-size:10pt;}")

    w = QWidget()
    w.setWindowTitle("直角矩形 SwitchButton 演示")
    lay = QHBoxLayout(w)

    sw = QSwitchButton()
    label = QLabel("关闭")

    def on_toggled(on):
        label.setText("开启" if on else "关闭")

    sw.toggled.connect(on_toggled)
    lay.addWidget(sw)
    lay.addWidget(label)
    w.resize(200, 60)
    w.show()
    app.exec_()