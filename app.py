from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

AVAILABLE_WIDTHS = [25, 30, 35, 40, 44, 50, 55, 60, 64, 70, 74, 80, 84, 90, 100, 104, 110]

def calculate_optimal_cutting(material_width: int, target_width: int, quantity: int) -> dict:
    """
    Calculate optimal cutting pattern for rolls
    """
    if not (500 <= material_width <= 910):
        return {"error": "Ширина материала должна быть от 500 до 910 мм"}

    if target_width not in AVAILABLE_WIDTHS:
        return {"error": "Выбранная ширина рулона недопустима"}

    # Вычисляем максимальное количество рулонов основной ширины
    max_rolls = material_width // target_width
    remaining_width = material_width % target_width

    best_combination = {
        "main_width": target_width,
        "main_count": max_rolls,
        "additional_width": None,
        "additional_count": 0,
        "waste": remaining_width,
        "sets_needed": math.ceil(quantity / max_rolls)
    }

    # Проверяем возможность добавления дополнительного рулона
    for width in AVAILABLE_WIDTHS:
        if width <= remaining_width:
            new_waste = remaining_width - width
            if new_waste < best_combination["waste"]:
                best_combination["additional_width"] = width
                best_combination["additional_count"] = 1
                best_combination["waste"] = new_waste

    return best_combination

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        try:
            material_width = int(request.form.get('material_width', 0))
            target_width = int(request.form.get('target_width', 0))
            quantity = int(request.form.get('quantity', 0))

            result = calculate_optimal_cutting(material_width, target_width, quantity)
        except ValueError:
            result = {"error": "Пожалуйста, введите корректные числовые значения"}

    return render_template('index.html', 
                         available_widths=AVAILABLE_WIDTHS,
                         result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)