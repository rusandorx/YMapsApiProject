import os
import sys

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QLineEdit, \
    QRadioButton

SCREEN_SIZE = [600, 450]


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.zoom = 1
        self.coords = (37.617644, 55.755819)
        self.map_type = 'map'
        self.point = None
        self.show_post_code = False
        self.toponym = None

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
        if event.key() in (Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            self.getImage()
            self.update_image()

    def mousePressEvent(self, event):
        x, y = event.x(), event.y()
        if event.button() == Qt.LeftButton and 10 < x < SCREEN_SIZE[0] - 10 and 10 < y < SCREEN_SIZE[1] - 10:
            x, y = x - 10 - SCREEN_SIZE[0] // 2, y - 10 - SCREEN_SIZE[1] // 2
            self.coords = (self.coords[0] + x * self.zoom / 360, self.coords[1] - y * self.zoom / 360)
            self.getImage()
            self.update_image()

    def getImage(self):
        geocoder_params = {
            'll': ','.join(map(str, self.coords)),
            'spn': str(self.zoom) + ',0.00619',
            'l': self.map_type,
            'pt': ','.join(map(str, self.point)) + ',pm2ntl' if self.point else None
        }
        map_request = f"http://static-maps.yandex.ru/1.x/"
        response = requests.get(map_request, params=geocoder_params)

        if not response:
            print("Ошибка выполнения запроса:")
            print(map_request)
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)

        self.map_file = "map.png"
        with open(self.map_file, "wb") as file:
            file.write(response.content)

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        self.setGeometry(100, 100, *SCREEN_SIZE)
        self.setWindowTitle('Отображение карты')
        self.update_image()

        self.btns_layout = QHBoxLayout(self)
        for label in ('map', 'sat', 'sat,skl'):
            btn = QPushButton(self)
            btn.setText(label)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(Example.decorate(self.change_map_type, label))
            self.btns_layout.addWidget(btn)

        self.search_layout = QHBoxLayout(self)
        self.search_field = QLineEdit(self)
        self.search_field.setFocusPolicy(Qt.ClickFocus)

        self.search_button = QPushButton(self)
        self.search_button.setText('Найти')
        self.search_button.setFocusPolicy(Qt.NoFocus)
        self.search_button.clicked.connect(self.search)
        self.post_code_switch = QRadioButton(self)
        self.post_code_switch.setText('Показывать почтовый индекс')
        self.post_code_switch.toggled.connect(self.toggle_post_code)
        self.search_layout.addWidget(self.search_field)
        self.search_layout.addWidget(self.search_button)
        self.search_layout.addWidget(self.post_code_switch)

        self.clear_btn = QPushButton(self)
        self.clear_btn.setText('Сброс поискового результата')
        self.clear_btn.setFocusPolicy(Qt.NoFocus)
        self.clear_btn.clicked.connect(self.clear_search)

        self.address_field = QLabel(self)

        self.main_layout.addWidget(self.image)
        self.main_layout.addLayout(self.btns_layout)
        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addWidget(self.clear_btn)
        self.main_layout.addWidget(self.address_field)

    def toggle_post_code(self, enabled):
        self.show_post_code = enabled
        if not self.address_field.text():
            return
        if enabled:
            address = self.toponym['metaDataProperty']['GeocoderMetaData']['Address']
            post_code = address['postal_code'] + ' ' if self.show_post_code and 'postal_code' in address else ''
            self.address_field.setText(post_code + self.address_field.text())
        else:
            self.address_field.setText(self.toponym['metaDataProperty']['GeocoderMetaData']['text'])

    def update_image(self):
        self.pixmap = QPixmap(self.map_file)
        self.image.resize(600, 450)
        self.image.setPixmap(self.pixmap)

    def search(self):
        toponym_to_find = self.search_field.text()
        self.search_field.clearFocus()

        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

        geocoder_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": toponym_to_find,
            "format": "json"}

        response = requests.get(geocoder_api_server, params=geocoder_params)

        json_response = response.json()
        if not json_response["response"]["GeoObjectCollection"]["featureMember"]:
            print('Ничего не найдено')
            return

        toponym = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        self.toponym = toponym
        address = toponym['metaDataProperty']['GeocoderMetaData']['Address']
        post_code = address['postal_code'] + ' ' if self.show_post_code and 'postal_code' in address else ''
        text = post_code + toponym['metaDataProperty']['GeocoderMetaData']['text']
        self.address_field.setText(text)
        self.coords = tuple(map(float, toponym["Point"]["pos"].split()))
        self.point = self.coords
        self.getImage()
        self.update_image()

    def clear_search(self):
        self.point = None
        self.address_field.setText('')
        self.getImage()
        self.update_image()

    def change_map_type(self, new_type):
        self.map_type = new_type
        self.getImage()
        self.update_image()

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
