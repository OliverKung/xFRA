from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton,QLabel, QDialog, QFrame
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt
from basic_custom_widget.QLabelComboBox import QLabelComboBox
from basic_custom_widget.QEngLineEdit import QEngLineEdit


class FramedWidget(QWidget):
    """自定义控件：在本身尺寸内绘制蓝色边框，内部再嵌一个垂直布局放按钮"""
    def __init__(self, parent=None,color = "#1E90FF"):
        super().__init__(parent)
        # self.setFixedSize(160, 180)          # 根据需要调整大小
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.color = color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color), 4)   # 4 像素宽的蓝色边框
        #虚线边框
        # pen.setStyle(Qt.DotLine)
        painter.setPen(pen)
        # 在控件矩形内画边框
        painter.drawRect(self.rect())

class channelSet(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self.on_sync_trigger_toggled(self.syncTriggerCheckBox.isChecked())
        self.syncTriggerCheckBox.clicked.connect(self.on_sync_trigger_toggled)

    def on_sync_trigger_toggled(self, checked):
        if checked:
            self.SyncExctChannelSelect.setEnabled(True)
            self.SyncExctInputImp.setEnabled(True)
            self.SyncMeasBandwidthLimit.setEnabled(True)
            self.SyncMeasChannelSelect.setEnabled(True)
            self.SyncMeasInputImp.setEnabled(True)
            self.SyncMeasCouple.setEnabled(True)
        else:
            self.SyncExctChannelSelect.setEnabled(False)
            self.SyncExctInputImp.setEnabled(False)
            self.SyncMeasBandwidthLimit.setEnabled(False)
            self.SyncMeasChannelSelect.setEnabled(False)
            self.SyncMeasCouple.setEnabled(False)
            self.SyncMeasInputImp.setEnabled(False)

    def _build_ui(self):
        self.setWindowTitle("xFRA E-M Class Channel Set")
        self.setWindowIcon(QtGui.QIcon("./icon/xFRA_ProbeSet.png"))
        self.setObjectName("Dialog")
        self.setFixedSize(720, 480)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setFamily("Arial")
        font.setWeight(75)
        self.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.label = QLabel("Channel Set", self)
        self.label.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label)

        self.MeasSetGridWidget = FramedWidget(self,color="#1E90FF")
        self.MeasSetGridLayout = QtWidgets.QGridLayout(self.MeasSetGridWidget)
        self.MeasSetGridWidget.setLayout(self.MeasSetGridLayout)
        self.verticalLayout.addWidget(self.MeasSetGridWidget)
        self.Meas1ChannelSelect = QLabelComboBox(label_text="Meas1 Channel",combo_items=["CH1", "CH2", "CH3", "CH4"])
        self.MeasSetGridLayout.addWidget(self.Meas1ChannelSelect, 0, 0)
        self.Meas1Couple = QLabelComboBox(label_text="Couple",combo_items=["DC","AC","GND"])
        self.MeasSetGridLayout.addWidget(self.Meas1Couple, 0, 1)
        self.Meas2ChannelSelect = QLabelComboBox(label_text="Meas2 Channel",combo_items=["CH1", "CH2", "CH3", "CH4"]) 
        self.MeasSetGridLayout.addWidget(self.Meas2ChannelSelect, 1, 0)
        self.Meas2Couple = QLabelComboBox(label_text="Couple",combo_items=["DC","AC","GND"])
        self.MeasSetGridLayout.addWidget(self.Meas2Couple, 1, 1)
        self.Meas2InputImp = QLabelComboBox(label_text="Imp",combo_items=["1 MΩ", "50 Ω"])
        self.MeasSetGridLayout.addWidget(self.Meas2InputImp, 0, 2)
        self.Meas1InputImp = QLabelComboBox(label_text="Imp",combo_items=["1 MΩ", "50 Ω"])
        self.MeasSetGridLayout.addWidget(self.Meas1InputImp, 1, 2)
        self.SyncMeasChannelSelect = QLabelComboBox(label_text="SyncT Channel",combo_items=["CH1", "CH2", "CH3", "CH4"])
        self.MeasSetGridLayout.addWidget(self.SyncMeasChannelSelect, 2, 0)
        self.SyncMeasCouple = QLabelComboBox(label_text="Couple",combo_items=["DC","AC","GND"])
        self.MeasSetGridLayout.addWidget(self.SyncMeasCouple, 2, 1)
        self.SyncMeasInputImp = QLabelComboBox(label_text="Imp",combo_items=["1 MΩ", "50 Ω"])
        self.MeasSetGridLayout.addWidget(self.SyncMeasInputImp, 2, 2)
        self.Meas1BandwidthLimit = QLabelComboBox(label_text="BW",combo_items=["Full"])
        self.MeasSetGridLayout.addWidget(self.Meas1BandwidthLimit, 0, 3)
        self.Meas2BandwidthLimit = QLabelComboBox(label_text="BW",combo_items=["Full"])
        self.MeasSetGridLayout.addWidget(self.Meas2BandwidthLimit, 1, 3)
        self.SyncMeasBandwidthLimit = QLabelComboBox(label_text="BW",combo_items=["Full"])
        self.MeasSetGridLayout.addWidget(self.SyncMeasBandwidthLimit, 2, 3)
       
        self.ExctSetGridWidget = FramedWidget(self,color="#EB0909")
        self.ExctSetVercticalLayout = QtWidgets.QVBoxLayout()
        self.ExctSetGridWidget.setLayout(self.ExctSetVercticalLayout)
        self.verticalLayout.addWidget(self.ExctSetGridWidget)
        self.ExctHBoxLayout = QtWidgets.QHBoxLayout()
        self.ExctSetVercticalLayout.addLayout(self.ExctHBoxLayout)
        self.ExcitationChannelSelect = QLabelComboBox(label_text="Excit Channel",combo_items=["CH1", "CH2"])
        self.ExctHBoxLayout.addWidget(self.ExcitationChannelSelect)
        self.ExcitationInputImp = QLabelComboBox(label_text="Imp",combo_items=["HiZ", "50 Ω"])
        self.ExctHBoxLayout.addWidget(self.ExcitationInputImp)
        self.SyncHBoxLayout = QtWidgets.QHBoxLayout()
        self.ExctSetVercticalLayout.addLayout(self.SyncHBoxLayout)
        self.SyncExctChannelSelect = QLabelComboBox(label_text="Sync Channel",combo_items=["CH1", "CH2"])
        self.SyncHBoxLayout.addWidget(self.SyncExctChannelSelect)
        self.SyncExctInputImp = QLabelComboBox(label_text="Imp",combo_items=["HiZ", "50 Ω"])
        self.SyncHBoxLayout.addWidget(self.SyncExctInputImp)
        self.syncTriggerCheckBox = QtWidgets.QCheckBox("SyncT on Excit", self)
        self.ExctSetVercticalLayout.addWidget(self.syncTriggerCheckBox)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout.setStretch(0, 4)
        self.verticalLayout.setStretch(1, 8)
        self.verticalLayout.setStretch(2, 6)
        self.verticalLayout.setStretch(3, 1)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
    def accept(self):
        print("Settings accepted")
        self.get_channel_settings()
        self.close()
    def reject(self):
        print("Settings canceled")
        self.close()
    
    def load_channel_settings(self, ch: dict):
        """Restore channel settings from a saved dict."""
        m1 = ch.get("Meas1", {})
        self.Meas1ChannelSelect.setCurrentText(m1.get("Channel", "CH1"))
        self.Meas1Couple.setCurrentText(m1.get("Couple", "DC"))
        self.Meas1InputImp.setCurrentText(m1.get("InputImp", "1 MΩ"))
        self.Meas1BandwidthLimit.setCurrentText(m1.get("BandwidthLimit", "Full"))
        m2 = ch.get("Meas2", {})
        self.Meas2ChannelSelect.setCurrentText(m2.get("Channel", "CH2"))
        self.Meas2Couple.setCurrentText(m2.get("Couple", "DC"))
        self.Meas2InputImp.setCurrentText(m2.get("InputImp", "1 MΩ"))
        self.Meas2BandwidthLimit.setCurrentText(m2.get("BandwidthLimit", "Full"))
        sm = ch.get("SyncMeas", {})
        self.SyncMeasChannelSelect.setCurrentText(sm.get("Channel", "CH1"))
        self.SyncMeasCouple.setCurrentText(sm.get("Couple", "DC"))
        self.SyncMeasInputImp.setCurrentText(sm.get("InputImp", "1 MΩ"))
        self.SyncMeasBandwidthLimit.setCurrentText(sm.get("BandwidthLimit", "Full"))
        ex = ch.get("Excit", {})
        self.ExcitationChannelSelect.setCurrentText(ex.get("Channel", "CH1"))
        self.ExcitationInputImp.setCurrentText(ex.get("InputImp", "HiZ"))
        se = ch.get("SyncExct", {})
        self.SyncExctChannelSelect.setCurrentText(se.get("Channel", "CH1"))
        self.SyncExctInputImp.setCurrentText(se.get("InputImp", "HiZ"))
        self.syncTriggerCheckBox.setChecked(se.get("Enabled", False))
        self.on_sync_trigger_toggled(se.get("Enabled", False))

    def get_channel_settings(self):
        settings = {
            "Meas1": {
                "Channel": self.Meas1ChannelSelect.currentText(),
                "Couple": self.Meas1Couple.currentText(),
                "InputImp": self.Meas1InputImp.currentText(),
                "BandwidthLimit": self.Meas1BandwidthLimit.currentText()
            },
            "Meas2": {
                "Channel": self.Meas2ChannelSelect.currentText(),
                "Couple": self.Meas2Couple.currentText(),
                "InputImp": self.Meas2InputImp.currentText(),
                "BandwidthLimit": self.Meas2BandwidthLimit.currentText()
            },
            "SyncMeas": {
                "Channel": self.SyncMeasChannelSelect.currentText(),
                "Couple": self.SyncMeasCouple.currentText(),
                "InputImp": self.SyncMeasInputImp.currentText(),
                "BandwidthLimit": self.SyncMeasBandwidthLimit.currentText()
            },
            "Excit": {
                "Channel": self.ExcitationChannelSelect.currentText(),
                "InputImp": self.ExcitationInputImp.currentText()
            },
            "SyncExct": {
                "Channel": self.SyncExctChannelSelect.currentText(),
                "InputImp": self.SyncExctInputImp.currentText(),
                "Enabled": self.syncTriggerCheckBox.isChecked()
            }
        }
        print(type(settings))
        print(settings)
        return settings
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = channelSet()
    dialog.show()
    sys.exit(app.exec_())