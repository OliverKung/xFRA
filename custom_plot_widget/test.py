from pyqtgraph.Qt import QtWidgets
import sys, numpy as np
from waveWidget import waveWidget

app = QtWidgets.QApplication([])

f = np.logspace(1, 11, 801)          # 1 MHz – 10 GHz
s21 = 1 / (1 + 1j * f / 3e9) ** 3
s31 = 1 / (1 + 1j * f / 1e8) ** 3

# 对数坐标（默认）
w_log = waveWidget(freq_axis='log')
w_log.add_trace('S21', f, 20 * np.log10(np.abs(s21) + 1e-12))
w_log.add_trace('S31', f, 20 * np.log10(np.abs(s31) + 1e-12))
w_log.setWindowTitle('S21 Log Frequency')
w_log.show()

sys.exit(app.exec())