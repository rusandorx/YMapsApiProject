import os
import sys

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton

SCREEN_SIZE = [600, 450]


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.zoom = 1
        self.coords = (37.617644, 55.755819)
        self.map_type = 'map'

        self.image = QLabel(self)
        self.getImage()
        self.initUI()
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_PageUp:
            if self.zoom <= 5:
                self.zoom /= 0.5
        if event.key() == Qt.Key_PageDown:
            if self.zoom >= 0.02:
                self.zoom *= 0.5
        if event.key() == Qt.Key_Up:
            self.coords = (self.coords[0], self.coords[1] + self.zoom)
        if event.key() == Qt.Key_Down:
            self.coords = (self.coords[0], self.coords[1] - self.zoom)
        if event.key() == Qt.Key_Left:
            self.coords = (self.coords[0] - self.zoom, self.coords[1])
        if event.key() == Qt.Key_Right:
            self.coords = (self.coords[0] + self.zoom, self.coords[1])
        self.getImage()
        self.initUI()

    def getImage(self):
        map_request = f"http://static-maps.yandex.ru/1.x/?&ll={','.join(map(str, self.coords))}&spn={self.zoom},0.00619&l={self.map_type}"
        response = requests.get(map_request)

        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        self.map_file = "map.png"
        with open(self.map_file, "wb") as file:
            file.write(response.content)

    def initUI(self):
        self.setGeometry(100, 100, *SCREEN_SIZE)
        self.setWindowTitle('Отображение карты')
        self.pixmap = QPixmap(self.map_file)
        self.image.move(0, 0)
        self.image.resize(600, 450)
        self.image.setPixmap(self.pixmap)

        self.map_type_btns = []
        for label in ('map', 'sat', 'hybrid'):
            btn = QPushButton(self)
            btn.setText(label)
            btn.clicked.connect(Example.decorate(self.change_map_type, label))


    def change_map_type(self, new_type):
        self.map_type = new_type
        self.getImage()
        self.initUI()


    @staticmethod
    def decorate(func, obj):
        def new_func():
            return func(obj)

        return new_func

    def closeEvent(self, event):
        os.remove(self.map_file)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
