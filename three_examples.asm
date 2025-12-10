; Пример 1: Копирование массива
LOAD 1000, 10
LOAD 100, 11
LOAD 200, 12
LOAD 300, 13
STORE 1000, 11
STORE 1001, 12
STORE 1002, 13

; Пример 2: Арифметика с ROTR
LOAD 0xFFFFFFFF, 20
LOAD 16, 21
STORE 500, 21
LOAD 500, 22
ROTR 20, 22  ; Сдвиг на 16 бит

; Пример 3: Работа с памятью
LOAD 777, 30
LOAD 888, 31
LOAD 999, 32
STORE 600, 30
STORE 601, 31
STORE 602, 32
LOAD 600, 33
READ 40, 33  ; R40 = 777