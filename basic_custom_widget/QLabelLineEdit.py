from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication, QLineEdit
from PyQt5.QtCore import pyqtSignal


class QLabelLineEdit(QWidget):
    # 自定义信号，与 QlineEditBox 的 currentTextChanged 兼容
    textChanged = pyqtSignal(str)

    def __init__(self, label_text="", parent=None):
        super().__init__(parent)

        self.label = QLabel(label_text)
        self.lineEdit = QLineEdit()

        # 连接信号
        self.lineEdit.textChanged.connect(self.textChanged.emit)

        # 布局
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.lineEdit)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    # 设置整个控件的可见性
    def setVisible(self, visible: bool):
        super().setVisible(visible)
        
    # 获取当前文本
    def currentText(self):
        return self.lineEdit.text()

    # 设置 QLabel 的文本
    def setLabelText(self, text: str):
        self.label.setText(text)

    # 设置 lineEditBox 的选项
    def setlineEditText(self, text:str):
        self.lineEdit.clear()
        self.lineEdit.setText(text)
    # 获取 lineEditBox 的文本
    def text(self):
        return self.lineEdit.text()