# QIconButtonWidget.py
from PyQt5 import QtWidgets, QtGui, QtCore
from typing import Iterable


class QIconButtonWidget(QtWidgets.QWidget):
    """
    适用于 pyqtribbon-1.2.x 的“图标/文本/图标+文本”可切换按钮
    用法：
        widget = QIconButtonWidget(
                    parent,
                    texts=['Start','Pause','Stop'],
                    icons=[':/icons/start.png', ':/icons/pause.png', ':/icons/stop.png'],
                    mode='both'   # 可选 'icon' / 'text' / 'both'
                )
    然后 panel.addWidget(widget) 即可
    """

    def __init__(self,
                 parent=None,
                 texts: Iterable[str] = None,
                 icons: Iterable[str] = None,
                 mode: str = 'both'):
        super().__init__(parent)

        # region 参数校验
        if texts is None or icons is None:
            raise ValueError("texts 与 icons 必须同时传入")
        self._texts = list(texts)
        self._icons_path = list(icons)
        if len(self._texts) != len(self._icons_path):
            raise ValueError("texts 与 icons 长度必须一致")
        if mode not in {'icon', 'text', 'both'}:
            raise ValueError("mode 仅支持 'icon' / 'text' / 'both'")
        self._mode = mode
        # endregion

        # 1. 主按钮
        self._btn = QtWidgets.QToolButton(self)
        self._btn.setFixedSize(70, 70)                      # 大按钮尺寸
        self._btn.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)

        # 2. 加载图标
        self._icons = {txt: QtGui.QIcon(pth)
                       for txt, pth in zip(self._texts, self._icons_path)}

        # 3. 默认选中第一项
        self._current_key = self._texts[0]
        self._apply_mode()                                  # 按 mode 显示

        # 4. 下拉菜单
        self._menu = QtWidgets.QMenu(self)
        for t in self._texts:
            self._menu.addAction(
                self._icons[t], t, lambda k=t: self._switch_icon(k)
            )
        self._btn.setMenu(self._menu)

        # 5. 布局
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._btn)

    # -------------------------------------------------
    # public 接口
    # -------------------------------------------------
    def set_mode(self, mode: str):
        """运行期动态切换显示模式"""
        if mode not in {'icon', 'text', 'both'}:
            raise ValueError("mode 仅支持 'icon' / 'text' / 'both'")
        self._mode = mode
        self._apply_mode()

    # -------------------------------------------------
    # private
    # -------------------------------------------------
    def _apply_mode(self):
        """根据当前 mode 设置按钮样式"""
        if self._mode == 'icon':
            self._btn.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            self._btn.setIcon(self._icons[self._current_key])
        elif self._mode == 'text':
            self._btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
            self._btn.setText(self._current_key)
        else:  # both
            self._btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            self._btn.setIcon(self._icons[self._current_key])
            self._btn.setText(self._current_key)

    def _switch_icon(self, key: str):
        """切换选项并刷新显示"""
        if key == self._current_key:
            return
        self._current_key = key
        self._apply_mode()      # 重新按模式刷新