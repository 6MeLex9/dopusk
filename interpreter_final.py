"""
Финальная версия интерпретатора УВМ
"""

import json
import sys


class UVM:
    def __init__(self, memory_size=2048):
        self.memory_size = memory_size
        self.registers = [0] * 64
        self.memory = [0] * memory_size

    def decode_command(self, binary):
        """Декодирование 5-байтовой команды"""
        if len(binary) != 5:
            return 0, 0, 0

        a = binary[0]
        b = int.from_bytes(binary[1:4], 'little')
        c = binary[4]

        return a, b, c

    def execute_command(self, a, b, c):
        """Выполнение команды"""
        try:
            if a == 84:  # LOAD: загрузка константы B в регистр C
                if 0 <= c < 64:
                    self.registers[c] = b

            elif a == 223:  # READ: чтение из памяти
                # B - регистр-назначение, C - регистр с адресом
                if 0 <= c < 64:
                    mem_addr = self.registers[c]
                    if 0 <= mem_addr < len(self.memory):
                        if 0 <= b < 64:
                            self.registers[b] = self.memory[mem_addr]

            elif a == 9:  # STORE: запись в память
                # B - адрес в памяти, C - регистр-источник
                if 0 <= c < 64:
                    value = self.registers[c]
                    if 0 <= b < len(self.memory):
                        self.memory[b] = value

            elif a == 213:  # ROTR: циклический сдвиг
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
            print(f"Ошибка выполнения: A={a}, B={b}, C={c}: {e}")

    def run(self, binary_data):
        """Выполнение программы"""
        # Сброс
        self.registers = [0] * 64
        self.memory = [0] * self.memory_size

        # Выполнение
        for i in range(0, len(binary_data), 5):
            chunk = binary_data[i:i + 5]
            if len(chunk) < 5:
                break

            a, b, c = self.decode_command(chunk)
            self.execute_command(a, b, c)

    def get_memory_dump(self, start=0, end=200):
        """Дамп памяти"""
        dump = {}
        for addr in range(start, min(end, len(self.memory))):
            val = self.memory[addr]
            if val != 0:  # Показываем только ненулевые
                dump[f"0x{addr:04X}"] = val
        return dump

    def get_registers_dump(self):
        """Дамп регистров"""
        dump = {}
        for i, val in enumerate(self.registers):
            if val != 0:
                dump[f"R{i:02d}"] = val
        return dump


def run_program(binary_file, start_addr=0, end_addr=200):
    """Запуск программы"""
    with open(binary_file, 'rb') as f:
        binary = f.read()

    uvm = UVM()
    uvm.run(binary)

    print("=" * 50)
    print("ПРОГРАММА ВЫПОЛНЕНА УСПЕШНО!")
    print(f"Размер программы: {len(binary)} байт")
    print("=" * 50)

    # Регистры
    regs = uvm.get_registers_dump()
    if regs:
        print("\nРЕГИСТРЫ (ненулевые):")
        print("=" * 50)
        for reg, val in sorted(regs.items()):
            print(f"{reg}: {val:10d} (0x{val:08X})")

    # Память
    memory = uvm.get_memory_dump(start_addr, end_addr)
    if memory:
        print(f"\nПАМЯТЬ (адреса {start_addr}-{end_addr}, ненулевые):")
        print("=" * 50)
        for addr, val in sorted(memory.items()):
            print(f"{addr}: {val:10d} (0x{val:08X})")
    else:
        print(f"\nВ памяти {start_addr}-{end_addr} все значения нулевые")

    # Сохраняем в JSON
    dump = {
        "registers": regs,
        "memory": memory,
        "info": {
            "program_size": len(binary),
            "memory_range": f"{start_addr}-{end_addr}"
        }
    }

    with open("result.json", 'w') as f:
        json.dump(dump, f, indent=2)

    print(f"\nРезультат сохранен в result.json")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python interpreter_final.py program.bin [start] [end]")
        print("Пример: python interpreter_final.py program.bin 0 200")
        sys.exit(1)

    binary_file = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    end = int(sys.argv[3]) if len(sys.argv) > 3 else 200

    run_program(binary_file, start, end)