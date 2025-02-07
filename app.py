from flask import Flask, render_template, request, send_file
from fpdf import FPDF
import math
import os

app = Flask(__name__)

def create_pdf(result):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'static/fonts/DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    
    pdf.cell(0, 10, 'Результаты расчета:', ln=True)
    pdf.ln(5)
    
    if result.get('rolls_per_length'):
        pdf.cell(0, 10, f"Количество рулонов в запуске: {result['rolls_per_length']} шт.", ln=True)
    if result.get('material_length_needed'):
        pdf.cell(0, 10, f"Количество запусков: {result['material_length_needed']} шт.", ln=True)
    if result.get('stock_rolls'):
        pdf.cell(0, 10, f"Остается на складе: {result['stock_rolls']} шт.", ln=True)
    
    pdf.cell(0, 10, f"Основной размер: {result['main_width']} мм × {result['main_count']} шт.", ln=True)
    if result.get('additional_width'):
        pdf.cell(0, 10, f"Дополнительный размер: {result['additional_width']} мм × {result['additional_count']} шт.", ln=True)
    
    pdf.cell(0, 10, f"Отход по краям: {result['waste_per_side']:.1f} мм с каждой стороны", ln=True)
    pdf.cell(0, 10, f"Метраж намотки: {result['length']} м", ln=True)
    pdf.cell(0, 10, f"Общая площадь материала: {result['total_area']} м²", ln=True)
    pdf.cell(0, 10, f"Площадь готовых рулонов: {result['useful_area']} м²", ln=True)
    pdf.cell(0, 10, f"Площадь отходов: {result['waste_area']} м²", ln=True)
    
    filename = 'results.pdf'
    pdf.output(filename)
    return filename

# Допустимые значения ширины рулонов
ALLOWED_WIDTHS = [25, 30, 32.5, 35, 40, 44, 50, 55, 60, 63, 70, 74, 80, 84, 90, 94, 100, 104, 110, 120, 150]

def calculate_optimal_cutting(material_width: int, useful_width: int, target_width: float, length: float, rolls_needed: int = None) -> dict:
    """
    Calculate optimal cutting pattern for rolls
    """
    if not (500 <= material_width <= 910):
        return {"error": "Ширина материала должна быть от 500 до 910 мм"}

    if not (500 <= useful_width <= 910):
        return {"error": "Полезная ширина должна быть от 500 до 910 мм"}

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
        # Учитываем только основной размер при расчете необходимой длины
        material_length_needed = math.ceil(rolls_needed / best_combination["main_count"])
        best_combination["material_length_needed"] = material_length_needed

        # Расчет общего количества произведенных рулонов основного размера
        total_main_rolls = material_length_needed * best_combination["main_count"]

        # Расчет дополнительных рулонов на склад
        additional_rolls = 0
        if best_combination["additional_count"] > 0:
            additional_rolls = material_length_needed * best_combination["additional_count"]

        # Расчет излишков основного размера и добавление дополнительных рулонов
        best_combination["stock_rolls"] = (total_main_rolls - rolls_needed) + additional_rolls

    # Расчет площади отходов
    waste_width = best_combination["waste"]  # общая ширина отходов в мм
    waste_area = (waste_width / 1000) * length  # площадь отходов в м²

    # Учитываем количество запусков при расчете площади отходов
    if "material_length_needed" in best_combination:
        waste_area *= best_combination["material_length_needed"]

    best_combination["waste_area"] = round(waste_area, 2)

    # Обновляем общую площадь материала с учетом количества запусков
    if "material_length_needed" in best_combination:
        best_combination["total_area"] = round((material_width / 1000) * length * best_combination["material_length_needed"], 2)
        best_combination["useful_area"] = round(best_combination["useful_area"] * best_combination["material_length_needed"], 2)

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

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    result = request.get_json()
    if result and not result.get('error'):
        pdf_file = create_pdf(result)
        return send_file(pdf_file, as_attachment=True, download_name='results.pdf')
    return "Error generating PDF", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)