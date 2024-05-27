import sys
from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QFont

from PySide6.QtWidgets import QPushButton
def main():
    loader = QUiLoader()

    app = QtWidgets.QApplication(sys.argv)
    window = loader.load("./qtd/hwm_ui.ui", None)
    # new_widget = loader.load("./qtd/new_widget.ui", None)

    window.setWindowTitle("TEST")

    # window.tabWidget.setStyleSheet('''QTabBar::tab{width: 0; height: 0; margin: 0; padding: 0; border: none;}''')

    window.textBrowser.setTextColor('black')
    font = QFont()
    font.setPointSize(10)
    window.textBrowser.setFont(font)

    window.textBrowser.append(">> 16:53:01 Line 1")
    window.textBrowser.append(">> 16:53:01 Line 1")
    window.textBrowser.setTextColor('red')
    window.textBrowser.append(">> 16:53:01 Error")

    for i in range(0,100):
        window.textBrowser.append(f">> 16:53:01 Info {i}")

    # window.pushButton_2.setStyleSheet('QPushButton {background-color: rgb(94,131,204); border:  none}')
    # window.pushButton_2.setStyleSheet('')
    # window.pushButton_2.setFlat(1)

    window.show()

    app.exec()

if __name__ == '__main__':
    main()
