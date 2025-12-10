"""
Исправленный GUI для УВМ с рабочим интерпретатором
"""

import sys
import tempfile
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Подавляем предупреждение PyQt
import warnings

warnings.filterwarnings("ignore", message="sipPyTypeDict")

# Импортируем рабочие модули
from assembler import assemble_text_to_binary

# Импортируем UVM из interpreter_final.py
try:
    from interpreter_final import UVM
except ImportError:
    # Если не импортируется, создаем UVM прямо здесь
    class UVM:
        def __init__(self, memory_size=2048):
            self.memory_size = memory_size
            self.registers = [0] * 64
            self.memory = [0] * memory_size

        def decode_command(self, binary):
            if len(binary) != 5:
                return 0, 0, 0
            a = binary[0]
            b = int.from_bytes(binary[1:4], 'little')
            c = binary[4]
            return a, b, c

        def execute_command(self, a, b, c):
            try:
                if a == 84:  # LOAD
                    if 0 <= c < 64:
                        self.registers[c] = b
                elif a == 223:  # READ
                    if 0 <= c < 64:
                        mem_addr = self.registers[c]
                        if 0 <= mem_addr < len(self.memory):
                            if 0 <= b < 64:
                                self.registers[b] = self.memory[mem_addr]
                elif a == 9:  # STORE
                    if 0 <= c < 64:
                        value = self.registers[c]
                        if 0 <= b < len(self.memory):
                            self.memory[b] = value
                elif a == 213:  # ROTR
                    if 0 <= b < 64 and 0 <= c < 64:
                        mem_addr = self.registers[c]
                        if 0 <= mem_addr < len(self.memory):
                            shift = self.memory[mem_addr] & 0x1F
                            value = self.registers[b]
                            if shift > 0:
                                mask = 0xFFFFFFFF
                                result = ((value >> shift) | (value << (32 - shift))) & mask
                            else:
                                result = value
                            self.registers[b] = result
            except Exception as e:
                print(f"Ошибка выполнения: {e}")

        def run(self, binary_data):
            self.registers = [0] * 64
            self.memory = [0] * self.memory_size

            for i in range(0, len(binary_data), 5):
                chunk = binary_data[i:i + 5]
                if len(chunk) < 5:
                    break
                a, b, c = self.decode_command(chunk)
                self.execute_command(a, b, c)

        def get_memory_dump(self, start=0, end=200):
            dump = {}
            for addr in range(start, min(end, len(self.memory))):
                val = self.memory[addr]
                if val != 0:
                    dump[f"0x{addr:04X}"] = val
            return dump

        def get_registers_dump(self):
            dump = {}
            for i, val in enumerate(self.registers):
                if val != 0:
                    dump[f"R{i:02d}"] = val
            return dump


class UVMGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.binary_file_path = None
        self.temp_files = []

    def initUI(self):
        self.setWindowTitle("Учебная Виртуальная Машина (УВМ)")
        self.setGeometry(100, 100, 1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 1. Панель кнопок
        btn_panel = QHBoxLayout()

        self.test_btn = QPushButton("Тест из спецификации")
        self.test_btn.clicked.connect(self.load_spec_test)

        self.assemble_btn = QPushButton("Ассемблировать")
        self.assemble_btn.clicked.connect(self.assemble)

        self.run_btn = QPushButton("Выполнить")
        self.run_btn.clicked.connect(self.run)
        self.run_btn.setEnabled(False)

        btn_panel.addWidget(self.test_btn)
        btn_panel.addWidget(self.assemble_btn)
        btn_panel.addWidget(self.run_btn)
        btn_panel.addStretch()

        # 2. Редактор кода
        self.code_edit = QTextEdit()
        self.code_edit.setFont(QFont("Courier", 10))
        self.code_edit.setPlaceholderText("Введите программу на ассемблере...")

        # 3. Диапазон памяти
        range_panel = QHBoxLayout()
        range_panel.addWidget(QLabel("Диапазон памяти:"))

        self.start_edit = QLineEdit("0")
        self.start_edit.setFixedWidth(60)

        self.end_edit = QLineEdit("200")
        self.end_edit.setFixedWidth(60)

        range_panel.addWidget(self.start_edit)
        range_panel.addWidget(QLabel("-"))
        range_panel.addWidget(self.end_edit)
        range_panel.addStretch()

        # 4. Вкладки вывода
        self.tabs = QTabWidget()

        # Вкладка регистров
        self.registers_text = QTextEdit()
        self.registers_text.setReadOnly(True)
        self.registers_text.setFont(QFont("Courier", 9))
        self.tabs.addTab(self.registers_text, "Регистры")

        # Вкладка памяти
        self.memory_text = QTextEdit()
        self.memory_text.setReadOnly(True)
        self.memory_text.setFont(QFont("Courier", 9))
        self.tabs.addTab(self.memory_text, "Память")

        # Вкладка логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.tabs.addTab(self.log_text, "Логи")

        # Сборка интерфейса
        layout.addLayout(btn_panel)
        layout.addWidget(QLabel("Программа на ассемблере:"))
        layout.addWidget(self.code_edit, 2)
        layout.addLayout(range_panel)
        layout.addWidget(QLabel("Результаты:"))
        layout.addWidget(self.tabs, 3)

        # Загружаем тестовую программу
        self.load_spec_test()

    def log(self, message, color="black"):
        """Добавление сообщения в лог"""
        timestamp = QTime.currentTime().toString("HH:mm:ss")
        html = f'<font color="{color}">[{timestamp}] {message}</font><br>'
        current = self.log_text.toHtml()
        self.log_text.setHtml(html + current)

    def load_spec_test(self):
        """Загрузка тестовой программы из спецификации"""
        test_code = """; ТЕСТЫ ИЗ СПЕЦИФИКАЦИИ УВМ

; 1. LOAD 862, 19 → 54 5E 83 80 09
LOAD 862, 19

; 2. READ 43, 11 → DF EB 02 00 00
; Сначала подготовим память
LOAD 777, 11      ; R11 = 777 (адрес)
LOAD 999, 0       ; R0 = 999
STORE 777, 0      ; Память[777] = 999
READ 43, 11       ; R43 = Память[777] = 999

; 3. STORE 955, 60 → 09 BB 03 00 1E
LOAD 12345, 60    ; R60 = 12345
STORE 955, 60     ; Память[955] = 12345

; 4. ROTR 36, 48 → D5 24 0C 00 00
LOAD 0x00ABCDEF, 36  ; Тестовое значение
LOAD 8, 0           ; Сдвиг = 8
STORE 100, 0        ; Память[100] = 8
LOAD 100, 48        ; R48 = 100 (адрес сдвига)
ROTR 36, 48         ; Циклический сдвиг на 8
"""
        self.code_edit.setText(test_code)
        self.start_edit.setText("0")
        self.end_edit.setText("1000")
        self.log("Загружены тесты из спецификации УВМ", "blue")

    def assemble(self):
        """Ассемблирование программы"""
        code = self.code_edit.toPlainText()
        if not code.strip():
            self.log("Ошибка: нет кода для ассемблирования", "red")
            return

        try:
            binary_data, ir = assemble_text_to_binary(code, test_mode=False)

            if binary_data is None:
                self.log("Ошибка ассемблирования", "red")
                return

            # Сохраняем во временный файл
            temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin')
            temp_file.write(binary_data)
            temp_file.close()

            self.binary_file_path = temp_file.name
            self.temp_files.append(temp_file.name)

            # Включаем кнопку выполнения
            self.run_btn.setEnabled(True)

            # Выводим информацию
            self.log(f"Ассемблирование успешно! Размер: {len(binary_data)} байт", "green")
            self.log("Промежуточное представление:", "blue")

            for cmd in ir:
                self.log(f"  {cmd['mnemonic']} B={cmd['B']}, C={cmd['C']}")

            # Показываем байты
            hex_str = binary_data.hex()
            formatted = ' '.join(hex_str[i:i + 2].upper() for i in range(0, min(100, len(hex_str)), 2))
            if len(hex_str) > 100:
                formatted += " ..."
            self.log(f"Байты: {formatted}")

        except Exception as e:
            self.log(f"Ошибка при ассемблировании: {str(e)}", "red")

    def run(self):
        """Выполнение программы"""
        if not self.binary_file_path:
            self.log("Ошибка: сначала выполните ассемблирование", "red")
            return

        try:
            # Получаем диапазон
            start = int(self.start_edit.text())
            end = int(self.end_edit.text())

            if start >= end:
                self.log("Ошибка: некорректный диапазон", "red")
                return

            # Читаем бинарный файл
            with open(self.binary_file_path, 'rb') as f:
                binary_data = f.read()

            # Создаем и запускаем УВМ
            self.log("Запуск программы...", "blue")
            uvm = UVM(memory_size=2048)
            uvm.run(binary_data)

            # Получаем результаты
            registers = uvm.get_registers_dump()
            memory = uvm.get_memory_dump(start, end)

            # Выводим регистры
            self.registers_text.clear()
            if registers:
                self.registers_text.append("РЕГИСТРЫ (ненулевые):")
                self.registers_text.append("=" * 50)
                for reg in sorted(registers.keys()):
                    val = registers[reg]
                    self.registers_text.append(f"{reg}: {val:10d} (0x{val:08X})")
            else:
                self.registers_text.append("Все регистры нулевые")

            # Выводим память
            self.memory_text.clear()
            if memory:
                self.memory_text.append(f"ПАМЯТЬ (адреса {start}-{end}, ненулевые):")
                self.memory_text.append("=" * 50)
                for addr in sorted(memory.keys()):
                    val = memory[addr]
                    self.memory_text.append(f"{addr}: {val:10d} (0x{val:08X})")
            else:
                self.memory_text.append(f"В памяти {start}-{end} все значения нулевые")

            # Сохраняем в JSON
            result = {
                "registers": registers,
                "memory": memory,
                "info": {
                    "program_size": len(binary_data),
                    "memory_range": f"{start}-{end}"
                }
            }

            with open("gui_result.json", 'w') as f:
                json.dump(result, f, indent=2)

            self.log(f"Выполнение завершено! Результат сохранен в gui_result.json", "green")
            self.log(f"Затронутые адреса памяти: {list(memory.keys())}", "blue")

        except Exception as e:
            self.log(f"Ошибка выполнения: {str(e)}", "red")

    def closeEvent(self, event):
        """Очистка временных файлов при закрытии"""
        for temp_file in self.temp_files:
            try:
                import os
                os.unlink(temp_file)
            except:
                pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = UVMGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()