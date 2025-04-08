import sys
import random
import string
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, \
    QTableWidget, QTableWidgetItem
import pymysql
from barcode.codex import Code128
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.db_connection = self.connect_to_database()

    def initUI(self):
        self.setWindowTitle('Вход в систему')
        self.setGeometry(100, 100, 300, 200)
        layout = QVBoxLayout()
        self.username_label = QLabel('Логин:')
        self.username_input = QLineEdit()
        self.password_label = QLabel('Пароль:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_password_button = QPushButton('Показать пароль')
        self.show_password_button.setCheckable(True)
        self.show_password_button.clicked.connect(self.toggle_password_visibility)
        self.login_button = QPushButton('Войти')
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.show_password_button)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def connect_to_database(self):
        try:
            connection = pymysql.connect(
                host='localhost',
                user='root',  # Замените на вашего пользователя MySQL
                password='',  # Замените на ваш пароль MySQL
                database='laboratory2'  # Название вашей базы данных
            )
            return connection
        except pymysql.Error as err:
            QMessageBox.critical(self, 'Ошибка базы данных', f"Ошибка подключения к базе данных: {err}")
            return None

    def toggle_password_visibility(self):
        if self.show_password_button.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def attempt_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if self.db_connection:
            cursor = self.db_connection.cursor()
            query = "SELECT * FROM employee WHERE login = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            if user:
                self.open_main_window(user)
            else:
                QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')

    def open_main_window(self, user):
        self.main_window = MainWindow(user)
        self.main_window.show()
        self.close()


class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Основное окно')
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        self.user_info_label = QLabel(f'Добро пожаловать, {self.user[2]} {self.user[1]} ({self.user[9]})')
        layout.addWidget(self.user_info_label)
        self.order_button = QPushButton('Открыть заказы')
        self.order_button.clicked.connect(self.open_order_window)
        layout.addWidget(self.order_button)
        self.setLayout(layout)

    def open_order_window(self):
        self.order_window = OrderWindow(self)
        self.order_window.show()


class OrderWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Список заказов")
        self.setGeometry(100, 100, 600, 400)
        self.orders = [
            {"id": 1, "creating_date": "2025-02-03", "days": 2, "summ": "1700.00", "orderStatus_id": 1,
             "pacient_id": 2},
            {"id": 2, "creating_date": "2025-03-04", "days": 3, "summ": "2000.00", "orderStatus_id": 2,
             "pacient_id": 3},
        ]
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Дата создания", "Дни", "Сумма", "Статус"])
        self.populate_table()
        self.generate_btn = QPushButton("Создать штрих-код", self)
        self.generate_btn.clicked.connect(self.generate_barcode)
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(self.generate_btn)
        self.setLayout(layout)

    def populate_table(self):
        self.table.setRowCount(len(self.orders))
        for row, order in enumerate(self.orders):
            self.table.setItem(row, 0, QTableWidgetItem(str(order["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(order["creating_date"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(order["days"])))
            self.table.setItem(row, 3, QTableWidgetItem(order["summ"]))
            self.table.setItem(row, 4, QTableWidgetItem(str(order["orderStatus_id"])))

    def generate_barcode(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для генерации штрих-кода")
            return
        order_id = self.orders[selected_row]["id"]
        creating_date = self.orders[selected_row]["creating_date"]
        unique_code = ''.join(random.choices(string.digits, k=6))
        # Формируем данные для штрих-кода
        barcode_data = f"{order_id} {creating_date.replace('-', '')} {unique_code}"

        # Генерация штрих-кода
        code128 = Code128(barcode_data, writer=ImageWriter())

        # Сохраняем штрих-код в файл
        barcode_filename = f"barcode_{order_id}"
        code128.save(barcode_filename)

        # Создаем PDF с штрих-кодом
        pdf_filename = f"barcode_{order_id}.pdf"
        c = canvas.Canvas(pdf_filename, pagesize=A4)
        c.drawImage(f"{barcode_filename}.png", 100, 700, width=200, height=100)
        c.drawString(100, 680, f"Штрих-код для заказа {order_id}")
        c.save()
        QMessageBox.information(self, "Успех", f"Штрих-код сохранен в файл {pdf_filename}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())