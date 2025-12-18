import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QToolTip, QDialog, QFormLayout, 
                             QLineEdit, QDialogButtonBox, QMessageBox)
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont

from basic_custom_widget.QEngLineEdit import QEngLineEdit
from basic_custom_widget.QLabelLineEdit import QLabelLineEdit

# --- 弹出式编辑对话框 ---
class PointEditDialog(QDialog):
    def __init__(self, freq, amp, y_unit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Var Level Setting")
        # self.setStyleSheet("background-color: #333; color: white;")
        layout = QFormLayout(self)
        
        self.freq_input = QEngLineEdit(str(round(freq, 2)))
        self.amp_input = QEngLineEdit(str(round(amp, 2)))
        self.setFont(QFont("Arial", 10))
        layout.addRow("Frequency (Hz):", self.freq_input)
        layout.addRow(f"Amplitude ({y_unit}):", self.amp_input)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_values(self):
        try:
            return self.freq_input.get_value(), self.amp_input.get_value()
        except ValueError:
            return None

# --- 曲线编辑器核心类 ---
class AdvancedCurveEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化数据
        self.points = [QPointF(100, 20), QPointF(1000, 50), QPointF(10000, 80)]
        self.is_log_x = True
        self.y_unit = "dB"
        self.y_min, self.y_max = 0, 100
        self.x_min, self.x_max = 20, 20000
        
        self.selected_index = -1
        self.hover_index = -1
        self.margin_left = 70
        self.margin_bottom = 50
        self.margin_other = 30
        
        self.setMinimumSize(700, 450)
        self.setMouseTracking(True)

    # --- 修复：添加缺失的接口方法 ---
    def get_points(self):
        """获取所有点对 (频率, 幅度)"""
        sorted_pts = sorted(self.points, key=lambda p: p.x())
        return [(p.x(), p.y()) for p in sorted_pts]

    def set_x_log_mode(self, enabled: bool):
        self.is_log_x = enabled
        self.update()

    def set_y_range(self, y_min, y_max):
        self.y_min, self.y_max = y_min, y_max
        print("Y Range set to:", y_min, y_max)
        self.update()

    def set_y_unit(self, unit: str):
        self.y_unit = unit
        self.update()

    def set_x_range(self, x_min, x_max):
        self.x_min, self.x_max = x_min, x_max
        self.update()

    # --- 坐标映射逻辑 ---
    def _val_to_pixel(self, x_val, y_val):
        w = self.width() - self.margin_left - self.margin_other
        h = self.height() - self.margin_bottom - self.margin_other
        if self.is_log_x:
            norm_x = (np.log10(max(1, x_val)) - np.log10(self.x_min)) / (np.log10(self.x_max) - np.log10(self.x_min))
        else:
            norm_x = (x_val - self.x_min) / (self.x_max - self.x_min)
        norm_y = (y_val - self.y_min) / (self.y_max - self.y_min)
        px = self.margin_left + norm_x * w
        py = self.height() - self.margin_bottom - norm_y * h
        return QPointF(px, py)

    def _pixel_to_val(self, px, py):
        w = self.width() - self.margin_left - self.margin_other
        h = self.height() - self.margin_bottom - self.margin_other
        norm_x = max(0, min(1, (px - self.margin_left) / w))
        norm_y = max(0, min(1, (self.height() - self.margin_bottom - py) / h))
        if self.is_log_x:
            log_min, log_max = np.log10(self.x_min), np.log10(self.x_max)
            val_x = 10**(log_min + norm_x * (log_max - log_min))
        else:
            val_x = self.x_min + norm_x * (self.x_max - self.x_min)
        val_y = self.y_min + norm_y * (self.y_max - self.y_min)
        return val_x, val_y

    # --- 绘制逻辑 ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#F0F0F0"))
        
        grid_rect = QRectF(self.margin_left, self.margin_other, 
                           self.width() - self.margin_left - self.margin_other, 
                           self.height() - self.margin_bottom - self.margin_other)
        
        self._draw_grid(painter, grid_rect)
        
        # 绘制折线
        self.points.sort(key=lambda p: p.x())
        path_pts = [self._val_to_pixel(p.x(), p.y()) for p in self.points]
        painter.setPen(QPen(QColor("#0088D2"), 6))
        for i in range(len(path_pts) - 1):
            painter.drawLine(path_pts[i], path_pts[i+1])
            
        # 绘制数据点
        for i, pt in enumerate(path_pts):
            color = QColor("#006EB1") if i == self.hover_index else QColor("#0088D2")
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#006EB1"), 1))
            painter.drawEllipse(pt, 12, 12)

    def _draw_grid(self, painter, rect):
        painter.setPen(QPen(QColor("#929292"), 2, Qt.DotLine))
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        # Y轴刻度
        steps = 5
        for i in range(steps + 1):
            y_val = self.y_min + (self.y_max - self.y_min) * (i / steps)
            p = self._val_to_pixel(self.x_min, y_val)
            painter.drawLine(int(rect.left()), int(p.y()), int(rect.right()), int(p.y()))
            painter.setPen(QColor("#000000"))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(10, int(p.y() + 5), f"{y_val:g}{self.y_unit}")
            painter.setPen(QPen(QColor("#929292"), 2, Qt.DotLine))

        # X轴刻度
        if self.is_log_x:
            log_start = int(np.floor(np.log10(self.x_min)))
            log_end = int(np.ceil(np.log10(self.x_max)))
            for exp in range(log_start, log_end + 1):
                for sub in [1, 2, 5]: 
                    v = (10**exp) * sub
                    if self.x_min <= v <= self.x_max:
                        p = self._val_to_pixel(v, self.y_min)
                        label = f"{v/1000:g}k" if v >= 1000 else f"{v:g}"
                        painter.setPen(QPen(QColor("#929292"), 2, Qt.DotLine))
                        painter.drawLine(int(p.x()), int(rect.top()), int(p.x()), int(rect.bottom()))
                        painter.setPen(QColor("#000000"))
                        painter.setFont(QFont("Arial", 12))
                        painter.drawText(int(p.x() - 10), int(rect.bottom() + 20), label)
        else:
            for i in range(6):
                v = self.x_min + (self.x_max - self.x_min) * (i / 5)
                p = self._val_to_pixel(v, self.y_min)
                painter.setPen(QPen(QColor("#929292"), 2, Qt.DotLine))
                painter.drawLine(int(p.x()), int(rect.top()), int(p.x()), int(rect.bottom()))
                painter.setPen(QColor("#000000"))
                painter.setFont(QFont("Arial", 12))
                painter.drawText(int(p.x() - 15), int(rect.bottom() + 20), f"{int(v)}")

    # --- 交互事件 ---
    def mouseDoubleClickEvent(self, event):
        pos = event.pos()
        for i, p in enumerate(self.points):
            if (self._val_to_pixel(p.x(), p.y()) - QPointF(pos)).manhattanLength() < 15:
                dialog = PointEditDialog(p.x(), p.y(), self.y_unit, self)
                if dialog.exec_() == QDialog.Accepted:
                    vals = dialog.get_values()
                    if vals:
                        nx, ny = vals
                        self.points[i] = QPointF(max(self.x_min, min(self.x_max, nx)), 
                                                 max(self.y_min, min(self.y_max, ny)))
                        self.update()
                    else:
                        QMessageBox.warning(self, "输入错误", "请输入数字格式")
                return

    def mousePressEvent(self, event):
        pos = event.pos()
        for i, p in enumerate(self.points):
            if (self._val_to_pixel(p.x(), p.y()) - QPointF(pos)).manhattanLength() < 12:
                if event.button() == Qt.RightButton:
                    if len(self.points) > 1: self.points.pop(i); self.update()
                    return
                self.selected_index = i
                return
        if event.button() == Qt.LeftButton:
            vx, vy = self._pixel_to_val(pos.x(), pos.y())
            self.points.append(QPointF(vx, vy)); self.points.sort(key=lambda p: p.x()); self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.selected_index != -1 and event.buttons() & Qt.LeftButton:
            vx, vy = self._pixel_to_val(pos.x(), pos.y())
            self.points[self.selected_index] = QPointF(vx, vy); self.update()
        
        found = -1
        for i, p in enumerate(self.points):
            if (self._val_to_pixel(p.x(), p.y()) - QPointF(pos)).manhattanLength() < 12:
                found = i; break
        if found != self.hover_index: self.hover_index = found; self.update()

    def mouseReleaseEvent(self, event):
        self.selected_index = -1

class varLevelSetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Var Level Setting")
        self.setMinimumSize(400, 300)
        self.setFont(QFont("Arial", 12))
        layout = QVBoxLayout(self)
        
        self.curve_editor = AdvancedCurveEditor(self)
        layout.addWidget(self.curve_editor)
        
        btn_layout = QHBoxLayout()
        self.ymax = QLabelLineEdit("Amp Max")
        # self.ymax.setSuffix(self.curve_editor.y_unit)
        self.ymin = QLabelLineEdit("Amp Min")
        # self.ymin.setSuffix(self.curve_editor.y_unit)
        btn_layout.addWidget(self.ymax)
        btn_layout.addWidget(self.ymin)
        
        layout.addLayout(btn_layout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.ymax.textChanged.connect(self.update_y_range)
        self.ymin.textChanged.connect(self.update_y_range)
        layout.addWidget(self.buttons)
        # stop at here 2025年12月18日22点44分

    def accept(self):
        self.close()

    def reject(self):
        self.close()

    def update_y_range(self):
        try:
            y_max = float(self.ymax.currentText())
            y_min = float(self.ymin.currentText())
            if y_max > y_min:
                self.curve_editor.set_y_range(y_min, y_max)
        except ValueError:
            pass

    def get_points(self):
        points = self.curve_editor.get_points()
        return points

# --- 演示主程序 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = varLevelSetWindow()
    window.show()
    sys.exit(app.exec_())

    # app = QApplication(sys.argv)
    # demo = QWidget()
    # layout = QVBoxLayout(demo)
    
    # editor = AdvancedCurveEditor()
    # layout.addWidget(editor)
    
    # btn = QPushButton("打印当前所有点位 (Console)")
    # btn.clicked.connect(lambda: print("Points:", editor.get_points()))
    # layout.addWidget(btn)
    
    # demo.setWindowTitle("完整功能曲线编辑器 (PyQt5)")
    # demo.show()
    # sys.exit(app.exec_())