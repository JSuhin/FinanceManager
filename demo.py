"""
Test module
"""

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QVBoxLayout, QListWidget
from PyQt6.QtCore import QEvent


class DemoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Insert Context Menu to ListWidget')
        self.window_width, self.window_height = 800, 600
        self.setMinimumSize(self.window_width, self.window_height)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.listWidget = QListWidget()
        self.listWidget.addItems(('Facebook', 'Microsoft', 'Google'))
        self.listWidget.installEventFilter(self)
        layout.addWidget(self.listWidget)

        self.show()

    def eventFilter(self, source, event):

        if event.type() == QEvent.Type.ContextMenu and source is self.listWidget:
            menu = QMenu()
            menu.addAction("Novi unos")
            menu.addAction("Promijeni odabrani")
            menu.addAction("Izbriši")

            if menu.exec(event.globalPos()):
                if source.itemAt(event.pos()):
                    print(source.itemAt(event.pos()))
            return True
        return super().eventFilter(source, event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = DemoWidget()
    sys.exit(app.exec())
