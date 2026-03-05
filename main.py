import flet as ft
import google.generativeai as genai
import PIL.Image
import os
import datetime
import base64

# --- КОНФІГУРАЦІЯ ANDROID ---
# Використовуємо безпечне сховище для ключів та актів
safe_dir = os.environ.get("FLET_APP_STORAGE", ".")
key_file_path = os.path.join(safe_dir, "gemini_key.txt")
DEFAULT_API_KEY = "AIzaSyDHd-5YhrPFUk1Mht2Csfkn0-6xQa0dM2E" # Твій базовий ключ

system_instruction = """
Ти — провідний ветеринарно-санітарний інспектор-аналітик України. 
Твоя спеціалізація — контроль безпечності харчових продуктів.
База знань: Накази №16, №46, №28, №57, №1032, Закони №1870-IV, №771, КУпАП.
ПРАВИЛО ПРІОРИТЕТУ: Якщо людина-інспектор каже "Недоліків немає", ти встановлюєш ЗЕЛЕНИЙ ризик.
"""

def main(page: ft.Page):
    page.title = "VET-INSPECTOR AUDIT PRO"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    # window_width/height ВИДАЛЕНО (причина білого екрана)

    def get_saved_key():
        if os.path.exists(key_file_path):
            try:
                with open(key_file_path, "r") as f: return f.read().strip()
            except: pass
        return DEFAULT_API_KEY

    genai.configure(api_key=get_saved_key())
    selected_image_paths = []
    images_row = ft.Row(wrap=True, spacing=10)

    # --- UI ПАНЕЛЬ НАЛАШТУВАНЬ ---
    api_key_input = ft.TextField(label="Gemini API Key", value=get_saved_key(), password=True, can_reveal_password=True)
    def save_key(e):
        with open(key_file_path, "w") as f: f.write(api_key_input.value.strip())
        genai.configure(api_key=api_key_input.value.strip())
        page.close(settings_dialog)
        page.update()

    settings_dialog = ft.AlertDialog(title=ft.Text("Налаштування"), content=api_key_input, actions=[ft.TextButton("Зберегти", on_click=save_key)])

    # --- ЕЛЕМЕНТИ ІНТЕРФЕЙСУ ---
    title_row = ft.Row([
        ft.Text("PETROVET 49.0", size=20, weight="bold", color=ft.colors.BLUE_900),
        ft.IconButton(icon=ft.icons.SETTINGS, on_click=lambda _: page.open(settings_dialog))
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    object_dropdown = ft.Dropdown(label="Об'єкт", options=[ft.dropdown.Option(x) for x in ["М'ясо", "Молоко", "Риба", "Місце торгівлі"]], width=350)
    temp_input = ft.TextField(label="T °C", width=80)
    inspector_comment = ft.TextField(label="Коментар інспектора", width=250)
    risk_indicator = ft.Container(content=ft.Text("РИЗИК: НЕ ВИЗНАЧЕНО", color="white"), bgcolor="grey", padding=10, border_radius=5, alignment=ft.alignment.center)
    ai_res = ft.Markdown(value="*Очікування...*", selectable=True)

    fp = ft.FilePicker(on_result=lambda e: (
        [selected_image_paths.append(f.path) for f in e.files],
        [images_row.controls.append(ft.Image(src=f.path, width=90, height=90, fit="cover", border_radius=5)) for f in e.files],
        page.update()
    ) if e.files else None)
    page.overlay.append(fp)

    def analyze(e):
        if "пиво будеш" in inspector_comment.value.lower(): # Твій жарт
            ai_res.value = "## БЕЗ РОМАНА ВАСИЛЬОВИЧА НІ ! 🍻"; page.update(); return
        if not selected_image_paths: return
        ai_res.value = "⏳ *Аналіз...*"; page.update()
        try:
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
            imgs = [PIL.Image.open(p) for p in selected_image_paths]
            prompt = f"Об'єкт: {object_dropdown.value}, T: {temp_input.value}, Коментар: {inspector_comment.value}. Визнач ризик: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ], [РИЗИК_ЧЕРВОНИЙ]."
            response = model.generate_content([prompt] + imgs)
            text = response.text
            if "[РИЗИК_ЗЕЛЕНИЙ]" in text: risk_indicator.bgcolor, risk_indicator.content.value = "green", "РИЗИК: ЗЕЛЕНИЙ"
            elif "[РИЗИК_ЖОВТИЙ]" in text: risk_indicator.bgcolor, risk_indicator.content.value = "orange", "РИЗИК: ЖОВТИЙ"
            elif "[РИЗИК_ЧЕРВОНИЙ]" in text: risk_indicator.bgcolor, risk_indicator.content.value = "red", "РИЗИК: ЧЕРВОНИЙ"
            ai_res.value = text.replace("[РИЗИК_ЗЕЛЕНИЙ]", "").replace("[РИЗИК_ЖОВТИЙ]", "").replace("[РИЗИК_ЧЕРВОНИЙ]", "").strip()
        except Exception as ex: ai_res.value = f"❌ Помилка: {str(ex)}"
        page.update()

    def make_act(e):
        filename = f"AKT_{datetime.datetime.now().strftime('%H%M%S')}.html"
        path = os.path.join(safe_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"<html><body><h1>АКТ PETROVET</h1><p>{ai_res.value}</p></body></html>")
        page.open(ft.SnackBar(ft.Text(f"✅ Акт збережено: {filename}")))

    page.add(
        title_row,
        ft.Row([ft.ElevatedButton("📷 ФОТО", on_click=lambda _: fp.pick_files(allow_multiple=True)),
                ft.ElevatedButton("🔄 Скинути", on_click=lambda _: (selected_image_paths.clear(), images_row.controls.clear(), page.update()))]),
        images_row, object_dropdown, ft.Row([temp_input, inspector_comment]),
        ft.ElevatedButton("🔍 АНАЛІЗ", on_click=analyze, width=350, bgcolor=ft.colors.BLUE_900, color="white"),
        risk_indicator, ft.Divider(), ai_res,
        ft.ElevatedButton("📄 СКЛАСТИ АКТ", on_click=make_act, width=350, bgcolor="green", color="white")
    )

ft.app(target=main)
