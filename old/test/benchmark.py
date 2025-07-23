import time
import os
import sys

# Путь к директории, содержащей benchmark.py
this_dir = os.path.dirname(os.path.abspath(__file__))

# Путь к директории с модулями (old/)
parent_dir = os.path.abspath(os.path.join(this_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from oneImage import tmImage

# Путь к папке с тестовыми данными
DATA_DIR = "benchmark_test"
images = [f for f in os.listdir(DATA_DIR) if f.endswith(".JPG")]

results = []

print("== Benchmark: tmImage ==")
for img_name in sorted(images):
    full_path = os.path.join(DATA_DIR, img_name)
    print(f"\n📷 Обработка: {img_name}")

    # Замер времени инициализации
    t0 = time.time()
    im = tmImage(full_path)
    t1 = time.time()

    # Замер времени коррекции
    _ = im.imCorrect
    t2 = time.time()

    # Замер времени сохранения
    im.saveImCorrect()
    t3 = time.time()

    results.append({
        "image": img_name,
        "init": round(t1 - t0, 3),
        "correction": round(t2 - t1, 3),
        "save": round(t3 - t2, 3),
        "total": round(t3 - t0, 3)
    })

# Вывод таблицы
print("\n📊 Результаты:")
print(f"{'Изображение':<15} {'init':>6} {'corr':>6} {'save':>6} {'total':>6}")
for r in results:
    print(f"{r['image']:<15} {r['init']:>6} {r['correction']:>6} {r['save']:>6} {r['total']:>6}")
