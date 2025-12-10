#!/usr/bin/env python3
"""
Сборочный скрипт для УВМ
"""

import sys
import os
import subprocess
import platform


def build_gui():
    """Сборка GUI приложения"""
    system = platform.system()

    if system == "Windows":
        # PyInstaller для Windows
        subprocess.run(["pyinstaller", "--onefile", "--windowed",
                        "--name=UVM_Windows", "gui_fixed.py"])
        print("Собрано для Windows: dist/UVM_Windows.exe")

    elif system == "Linux":
        # PyInstaller для Linux
        subprocess.run(["pyinstaller", "--onefile",
                        "--name=UVM_Linux", "gui_fixed.py"])
        print("Собрано для Linux: dist/UVM_Linux")

    else:
        print(f"Система {system} не поддерживается для сборки")


def build_cli():
    """Сборка CLI версий"""
    # Ассемблер
    with open("uvm_assembler.py", "w") as f:
        f.write('''#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from assembler import main
if __name__ == "__main__":
    main()
''')

    # Интерпретатор
    with open("uvm_interpreter.py", "w") as f:
        f.write('''#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from interpreter_final import main
if __name__ == "__main__":
    main()
''')

    os.chmod("uvm_assembler.py", 0o755)
    os.chmod("uvm_interpreter.py", 0o755)
    print("CLI утилиты созданы: uvm_assembler.py, uvm_interpreter.py")


if __name__ == "__main__":
    print("Сборка Учебной Виртуальной Машины...")
    build_cli()

    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        build_gui()

    print("\nСборка завершена!")
    print("Использование:")
    print("  Ассемблер: python uvm_assembler.py input.asm output.bin [--test]")
    print("  Интерпретатор: python uvm_interpreter.py program.bin [start] [end]")
    print("  GUI: python gui_fixed.py")