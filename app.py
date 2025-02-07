from flask import Flask, render_template, request
import math

app = Flask(__name__)

# Допустимые значения ширины рулонов
ALLOWED_WIDTHS = [20, 25, 30, 32.5, 35, 40, 44, 50, 55, 60, 63, 70, 74, 80, 84, 90, 94, 100, 104, 110, 120, 150]

def calculate_optimal_cutting(material_width: int, useful_width: int, target_width: float, length: float, rolls_needed: int = None) -> dict:
    """
    Calculate optimal cutting pattern for rolls
    """
    if not (500 <= material_width <= 910):
        return {"error": "Ширина материала должна быть от 500 до 910 мм"}

    if not (500 <= useful_width <= material_width):
        return {"error": f"Полезная ширина должна быть от 500 мм до {material_width} мм"}

    if not (30 <= length <= 1100):
        return {"error": "Длина материала должна быть от 30 до 1100 метров"}

    if target_width not in ALLOWED_WIDTHS:
        return {"error": "Выбранная ширина не соответствует допустимым значениям"}

    # Вычисляем максимальное количество рулонов основной ширины
    max_rolls = int(useful_width // target_width)  # Округляем до целого числа
    remaining_width = useful_width % target_width

    # Общая площадь материала (в кв. метрах)
    total_area = (material_width / 1000) * length  # переводим мм в метры

    # Вычисляем отход по краям (разница между общей и полезной шириной)
    edge_waste = material_width - useful_width
    waste_per_side = edge_waste / 2

    best_combination = {
        "main_width": target_width,
        "main_count": max_rolls,
        "additional_width": None,
        "additional_count": 0,
        "waste": remaining_width + edge_waste,  # Общий отход включает отход по краям
        "material_width": material_width,
        "useful_width": useful_width,  # Добавляем полезную ширину для отображения
        "waste_per_side": waste_per_side,  # Отход на каждую сторону
        "length": length,
        "total_area": round(total_area, 2),
        "useful_area": round((target_width * max_rolls / 1000) * length, 2),
        "rolls_per_length": max_rolls,  # Количество рулонов с одного метра материала
    }

    # Проверяем возможность добавления дополнительного рулона
    potential_widths = []
    for width in ALLOWED_WIDTHS:
        if width <= remaining_width:
            new_waste = remaining_width - width
            potential_widths.append({
                "width": width,
                "waste": new_waste
            })

    if potential_widths:
        # Выбираем ширину с минимальным отходом
        best_width = min(potential_widths, key=lambda x: x["waste"])
        best_combination["additional_width"] = best_width["width"]
        best_combination["additional_count"] = 1
        best_combination["waste"] = best_width["waste"] + edge_waste  # Добавляем отход по краям
        best_combination["useful_area"] += round((best_width["width"] / 1000) * length, 2)
        best_combination["rolls_per_length"] += 1

    # Если указано необходимое количество рулонов, рассчитываем необходимую длину материала
    if rolls_needed:
        best_combination["rolls_needed"] = rolls_needed
        best_combination["material_length_needed"] = math.ceil(rolls_needed / best_combination["rolls_per_length"])

    return best_combination

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        try:
            material_width = int(request.form.get('material_width', 0))
            useful_width = int(request.form.get('useful_width', 0))
            target_width = float(request.form.get('target_width', 0))
            length = float(request.form.get('length', 0))
            rolls_needed = int(request.form.get('rolls_needed', 0) or 0)

            result = calculate_optimal_cutting(material_width, useful_width, target_width, length, 
                                            rolls_needed if rolls_needed > 0 else None)
        except ValueError:
            result = {"error": "Пожалуйста, введите корректные числовые значения"}

    return render_template('index.html', allowed_widths=ALLOWED_WIDTHS, result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)