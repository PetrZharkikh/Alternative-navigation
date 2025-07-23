import cv2
import numpy as np
import json
import os

# Создание директории
output_dir = "benchmark_test"
os.makedirs(output_dir, exist_ok=True)

# === 1. Генерация изображений ===
for i in range(3):
    # Создаем "пейзаж" с рельефом
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)

    # Рисуем простые объекты
    cv2.line(img, (100+i*50, 200+i*30), (1800-i*60, 1000-i*50), (0, 255, 0), 8)
    cv2.circle(img, (960+i*20, 540+i*10), 100, (255, 255, 0), -1)
    cv2.putText(img, f"Frame {i+1}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)

    # Сохраняем изображение
    filename = f"DJI_000{i+1}.JPG"
    path = os.path.join(output_dir, filename)
    cv2.imwrite(path, img)
    print(f"[✓] Сохранено изображение: {filename}")

# === 2. Параметры полета (телеметрия) ===
params = {
    f"DJI_000{i+1}.JPG": {
        "lat": 55.751244 + i * 0.0005,
        "lon": 37.618423 + i * 0.0005,
        "height": 100.0,
        "azimuth": 90.0 + i * 5,
        "pitch": -30.0,
        "roll": 0.0,
        "yaw": 0.0,
        "cam_angle": 45.0
    } for i in range(3)
}

# Сохраняем как JSON
with open(os.path.join(output_dir, "params.json"), "w") as f:
    json.dump(params, f, indent=4)

print(f"[✓] Сохранён params.json")
print("\n📁 Данные готовы в папке: benchmark_test")
