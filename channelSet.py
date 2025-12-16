from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton,QLabel, QDialog
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtCore, QtGui, QtWidgets
from basic_custom_widget.QLabelComboBox import QLabelComboBox
from basic_custom_widget.QEngLineEdit import QEngLineEdit

class channelSet(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("Dialog")
        self.resize(640, 480)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setFamily("Arial")
        font.setWeight(75)
        self.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.label = QLabel("Channel Set Dialog", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label)

        self.MeasSetGridLayout = QtWidgets.QGridLayout()
        self.verticalLayout.addLayout(self.MeasSetGridLayout)
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
        self.buttonBox = QtWidgets.QDialogButtonBox(self)

        self.ExctSetGridLayout = QtWidgets.QGridLayout()
        self.verticalLayout.addLayout(self.ExctSetGridLayout)
        self.ExcitationChannelSelect = QLabelComboBox(label_text="Excit Channel",combo_items=["CH1", "CH2", "CH3", "CH4"])
        self.ExctSetGridLayout.addWidget(self.ExcitationChannelSelect, 0, 0)
        self.ExcitationCouple = QLabelComboBox(label_text="Couple",combo_items=["DC","AC","GND"])
        self.ExctSetGridLayout.addWidget(self.ExcitationCouple, 0, 1)
        self.ExcitationInputImp = QLabelComboBox(label_text="Imp",combo_items=["HiZ", "50 Ω"])
        self.ExctSetGridLayout.addWidget(self.ExcitationInputImp, 0, 2)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
        # self.buttonBox.accepted.connect(self.accept)
        # self.buttonBox.rejected.connect(self.reject)
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = channelSet()
    dialog.show()
    sys.exit(app.exec_())