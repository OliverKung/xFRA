from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QHBoxLayout, QApplication
from PyQt5.QtCore import pyqtSignal


class QLabelComboBox(QWidget):
    # 自定义信号，与 QComboBox 的 currentTextChanged 兼容
    currentTextChanged = pyqtSignal(str)
    mouseDoubleClicked = pyqtSignal()

    def __init__(self, label_text="", combo_items=None, parent=None):
        super().__init__(parent)

        self.label = QLabel(label_text)
        self.combo = QComboBox()

        if combo_items:
            self.combo.addItems(combo_items)

        # 连接信号
        self.combo.currentTextChanged.connect(self.currentTextChanged.emit)
        self.combo.mouseDoubleClickEvent = self._on_double_click

        # 布局
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
    # 双击事件处理
    def _on_double_click(self, event):
        self.mouseDoubleClicked.emit()

    # 设置整个控件的可见性
    def setVisible(self, visible: bool):
        super().setVisible(visible)

    # 获取当前选中的索引
    def currentIndex(self):
        return self.combo.currentIndex()

    # 设置当前选中的索引
    def setCurrentIndex(self, index: int):
        self.combo.setCurrentIndex(index)

    def setCurrentText(self, index: str):
        self.combo.setCurrentText(index)

    # 获取当前文本
    def currentText(self):
        return self.combo.currentText()

    # 设置 QLabel 的文本
    def setLabelText(self, text: str):
        self.label.setText(text)

    # 设置 ComboBox 的选项
    def setComboItems(self, items):
        self.combo.clear()
        self.combo.addItems(items)

    # 获取 ComboBox 的选项数量
    def count(self):
        return self.combo.count()
    # 获取指定索引的选项文本
    def itemText(self, index: int):
        return self.combo.itemText(index)

# 示例用法
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    widget = QLabelComboBox(
        label_text="选择项目：",
        combo_items=["选项1", "选项2", "选项3"]
    )

    # 连接信号
    def on_text_changed(text):
        print(f"当前选中文本：{text}")

    widget.currentTextChanged.connect(on_text_changed)

    widget.show()
    sys.exit(app.exec_())