import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.current_value = '0'
        self.stored_value = None
        self.pending_operator = None
        self.waiting_for_new_number = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Calculator')
        self.setFixedSize(360, 560)
        self.setStyleSheet('background-color: #000000;')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 24, 16, 16)
        main_layout.setSpacing(12)

        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.display.setFixedHeight(120)
        self.display.setStyleSheet(
            'color: white; font-size: 56px; font-weight: 300; padding: 0 8px;'
        )
        main_layout.addWidget(self.display)

        button_layout = QGridLayout()
        button_layout.setSpacing(10)

        buttons = [
            ['AC', '+/-', '%', '÷'],
            ['7', '8', '9', '×'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['0', '.', '='],
        ]

        for row_index, row in enumerate(buttons):
            for column_index, button_text in enumerate(row):
                button = self.create_button(button_text)

                if button_text == '0':
                    button_layout.addWidget(button, row_index, 0, 1, 2)
                elif row_index == 4:
                    button_layout.addWidget(button, row_index, column_index + 1)
                else:
                    button_layout.addWidget(button, row_index, column_index)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def create_button(self, text):
        button = QPushButton(text)
        button.setFixedHeight(64)
        button.clicked.connect(lambda: self.handle_button_click(text))

        if text in ['÷', '×', '-', '+', '=']:
            color = '#ff9500'
            text_color = '#ffffff'
        elif text in ['AC', '+/-', '%']:
            color = '#a5a5a5'
            text_color = '#000000'
        else:
            color = '#333333'
            text_color = '#ffffff'

        button.setStyleSheet(
            f'''
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 32px;
                font-size: 26px;
            }}
            QPushButton:pressed {{
                background-color: #d4d4d2;
            }}
            '''
        )
        return button

    def handle_button_click(self, text):
        # 버튼 종류에 따라 숫자 입력, 연산, 초기화를 처리한다.
        if text.isdigit():
            self.input_number(text)
        elif text == '.':
            self.input_decimal_point()
        elif text == 'AC':
            self.clear()
        elif text == '+/-':
            self.toggle_sign()
        elif text == '%':
            self.convert_to_percent()
        elif text in ['÷', '×', '-', '+']:
            self.set_operator(text)
        elif text == '=':
            self.calculate_result()

        self.update_display()

    def input_number(self, number):
        if self.current_value == '0' or self.waiting_for_new_number:
            self.current_value = number
            self.waiting_for_new_number = False
        else:
            self.current_value += number

    def input_decimal_point(self):
        if self.waiting_for_new_number:
            self.current_value = '0'
            self.waiting_for_new_number = False

        if '.' not in self.current_value:
            self.current_value += '.'

    def clear(self):
        self.current_value = '0'
        self.stored_value = None
        self.pending_operator = None
        self.waiting_for_new_number = False

    def toggle_sign(self):
        if self.current_value == '0':
            return

        if self.current_value.startswith('-'):
            self.current_value = self.current_value[1:]
        else:
            self.current_value = '-' + self.current_value

    def convert_to_percent(self):
        self.current_value = self.format_number(float(self.current_value) / 100)

    def set_operator(self, operator):
        if self.pending_operator and not self.waiting_for_new_number:
            self.calculate_result()

        self.stored_value = float(self.current_value)
        self.pending_operator = operator
        self.waiting_for_new_number = True

    def calculate_result(self):
        if self.pending_operator is None or self.stored_value is None:
            return

        current_number = float(self.current_value)

        if self.pending_operator == '+':
            result = self.stored_value + current_number
        elif self.pending_operator == '-':
            result = self.stored_value - current_number
        elif self.pending_operator == '×':
            result = self.stored_value * current_number
        elif self.pending_operator == '÷':
            if current_number == 0:
                self.current_value = 'Error'
                self.stored_value = None
                self.pending_operator = None
                self.waiting_for_new_number = True
                return
            result = self.stored_value / current_number

        self.current_value = self.format_number(result)
        self.stored_value = None
        self.pending_operator = None
        self.waiting_for_new_number = True

    def update_display(self):
        self.display.setText(self.current_value)

    def format_number(self, number):
        if number.is_integer():
            return str(int(number))
        return str(number).rstrip('0').rstrip('.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = Calculator()
    calculator.show()
    sys.exit(app.exec_())
