import time
import hashlib
import random

# 1️⃣ Blum-Blum-Shub (BBS)
def bbs_random(seed, p=499, q=547):
    """Генератор Blum-Blum-Shub (BBS)"""
    n = p * q  # Вычисляем модуль
    seed = (seed ** 2) % n  # Возводим seed в квадрат и берем остаток
    return seed % 900000 + 100000  # Генерируем 6-значное число

# 2️⃣ Линейный конгруэнтный метод (LCG)
def lcg_random(seed, a=1664525, c=1013904223, m=2**32):
    """Линейный конгруэнтный генератор (LCG)"""
    seed = (a * seed + c) % m
    return (seed % 900000) + 100000  # 6-значное число

# 3️⃣ Генератор на основе MD5-хэша
def md5_random(seed):
    """Генератор случайных чисел через хэш MD5"""
    hash_value = hashlib.md5(str(seed).encode()).hexdigest()  # Берем хэш
    return (int(hash_value[:6], 16) % 900000) + 100000  # Берем первые 6 цифр

# 4️⃣ Встроенный генератор Python (для сравнения)
def python_random():
    """Встроенный генератор random.randint()"""
    return random.randint(100000, 999999)

# 📌 Тестируем все генераторы
if __name__ == "__main__":
    seed = int(time.time())  # Берем текущее время как seed

    print(f"🔹 BBS: {bbs_random(seed)}")
    print(f"🔹 LCG: {lcg_random(seed)}")
    print(f"🔹 MD5: {md5_random(seed)}")
    print(f"🔹 Python Random: {python_random()}")
