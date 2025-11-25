from pyqtgraph.Qt import QtWidgets
import sys, numpy as np
from s21_widget import S21Widget

app = QtWidgets.QApplication([])

f = np.logspace(1, 11, 801)          # 1 MHz – 10 GHz
s21 = 1 / (1 + 1j * f / 3e9) ** 3

# 对数坐标（默认）
w_log = S21Widget(freq_axis='log')
w_log.set_data(f, s21)
w_log.setWindowTitle('S21 Log Frequency')
w_log.show()

sys.exit(app.exec())