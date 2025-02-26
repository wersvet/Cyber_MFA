import time

# Функция генерации псевдослучайного 6-значного кода через BBS
def bbs_random(seed, p=499, q=547):
    """Генератор Blum-Blum-Shub (BBS)"""
    n = p * q  # Вычисляем n
    seed = (seed ** 2) % n  # Возводим seed в квадрат и берем остаток
    return seed % 900000 + 100000  # Генерируем 6-значное число

# Получаем текущее время (будет использоваться как seed)
seed = int(time.time())
print(seed)

# Генерируем код
random_code = bbs_random(seed)

# Выводим результат
print(f"Сгенерированный 6-значный код: {random_code}")