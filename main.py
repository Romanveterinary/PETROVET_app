import flet as ft
import google.generativeai as genai
import PIL.Image
import os
import datetime
import base64

# --- ТЕХНІЧНА КОНФІГУРАЦІЯ ANDROID ---
safe_dir = os.environ.get("FLET_APP_STORAGE", ".")
key_file_path = os.path.join(safe_dir, "gemini_key.txt")

# Твій новий безкоштовний ключ
DEFAULT_API_KEY = "AIzaSyDHd-5YhrPFUk1Mht2Csfkn0-6xQa0dM2E"

system_instruction = """
Ти — провідний ветеринарно-санітарний інспектор-аналітик України. 
База знань: Накази №16, №46, №28, №57, №1032, Закони №1870-IV, №771, КУпАП.
ПРАВИЛО ПРІОРИТЕТУ: Якщо інспектор пише "Недоліків немає", став ЗЕЛЕНИЙ ризик.
"""

def main(page: ft.Page):
    page.title = "VET-INSPECTOR (PETROVET 49.0)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    # УВАГА: window_width/height видалено для стабільності на Android

    def get_saved_key():
        if os.path.exists(key_file_path):
            try:
                with open(key_file_path, "r") as f: return f.read().strip()
            except: pass
        return DEFAULT_API_KEY

    genai.configure(api_key=get_saved_key())
    selected_image_paths = []
    images_row = ft.Row(wrap=True, spacing=10)

    # --- НАЛАШТУВАННЯ API КЛЮЧА ---
    api_key_input = ft.TextField(label="Gemini API Key", value=get_saved_key(), password=True, can_reveal_password=True)
    
    def save_api_key(e):
        try:
            with open(key_file_path, "w") as f: f.write(api_key_input.value.strip())
            genai.configure(api_key=api_key_input.value.strip())
            page.close(settings_dialog)
            page.open(ft.SnackBar(ft.Text("✅ Ключ збережено!"), bgcolor="green"))
        except: pass
        page.update()

    settings_dialog = ft.AlertDialog(title=ft.Text("Налаштування"), content=api_key_input, actions=[ft.TextButton("Зберегти", on_click=save_api_key)])

    # --- UI ЕЛЕМЕНТИ ---
    title_row = ft.Row([
        ft.Text("PETROVET 49.0", size=20, weight="bold", color=ft.colors.BLUE_900),
        ft.IconButton(icon=ft.icons.SETTINGS, on_click=lambda _: page.open(settings_dialog))
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    object_dropdown = ft.Dropdown(
        label="Об'єкт контролю",
        options=[ft.dropdown.Option(x) for x in ["М'ясо (туші)", "Молоко/Сир", "Риба", "Місце торгівлі"]],
        width=350
    )
    
    temp_input = ft.TextField(label="T °C", width=80)
    inspector_comment = ft.TextField(label="Висновок інспектора", width=250, hint_text="Коментар...")
    
    risk_indicator = ft.Container(
        content=ft.Text("РИЗИК: НЕ ВИЗНАЧЕНО", color="white", weight="bold"),
        bgcolor="grey", padding=10, border_radius=5, width=350, alignment=ft.alignment.center
    )
    
    ai_response_text = ft.Markdown(value="*Очікування об'єкта...*", selectable=True)

    # --- ФАЙЛ ПІКЕР ---
    fp = ft.FilePicker(on_result=lambda e: (
        [selected_image_paths.append(f.path) for f in e.files],
        [images_row.controls.append(ft.Image(src=f.path, width=90, height=90, fit="cover", border_radius=5)) for f in e.files],
        page.update()
    ) if e.files else None)
    page.overlay.append(fp)

    def perform_analysis(e):
        if not selected_image_paths:
            ai_response_text.value = "❌ Додайте фото."; page.update(); return
            
        ai_response_text.value = "⏳ *Аналіз та юридичне обґрунтування...*"; page.update()

        try:
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
            pil_images = [PIL.Image.open(path) for path in selected_image_paths]
            
            prompt = f"Об'єкт: {object_dropdown.value}, T: {temp_input.value}, Коментар: {inspector_comment.value}. Визнач ризик: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ] або [РИЗИК_ЧЕРВОНИЙ]."
            
            response = model.generate_content([prompt] + pil_images)
            res = response.text
            
            if "[РИЗИК_ЗЕЛЕНИЙ]" in res:
                risk_indicator.bgcolor, risk_indicator.content.value = "green", "РІВЕНЬ РИЗИКУ: ЗЕЛЕНИЙ"
            elif "[РИЗИК_ЖОВТИЙ]" in res:
                risk_indicator.bgcolor, risk_indicator.content.value = "orange", "РІВЕНЬ РИЗИКУ: ЖОВТИЙ"
            elif "[РИЗИК_ЧЕРВОНИЙ]" in res:
                risk_indicator.bgcolor, risk_indicator.content.value = "red", "РІВЕНЬ РИЗИКУ: ЧЕРВОНИЙ"

            ai_response_text.value = res.replace("[РИЗИК_ЗЕЛЕНИЙ]", "").replace("[РИЗИК_ЖОВТИЙ]", "").replace("[РИЗИК_ЧЕРВОНИЙ]", "").strip()
        except Exception as ex:
            ai_response_text.value = f"❌ Помилка: {str(ex)}"
        page.update()

    def save_act(e):
        if not ai_response_text.value or "Очікування" in ai_response_text.value: return
        filename = f"AKT_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(safe_dir, filename)
        
        # Генерація HTML (базова структура)
        html = f"<html><body><h1>АКТ ОБСТЕЖЕННЯ</h1><p>{ai_response_text.value}</p></body></html>"
        with open(filepath, "w", encoding="utf-8") as f: f.write(html)
        page.open(ft.SnackBar(ft.Text(f"✅ Акт збережено: {filename}"), bgcolor="green"))

    # --- ВЕРСТКА ---
    page.add(
        title_row,
        ft.Row([ft.ElevatedButton("📷 ДОДАТИ ФОТО", icon=ft.icons.CAMERA_ALT, on_click=lambda _: fp.pick_files(allow_multiple=True)),
                ft.ElevatedButton("🔄 СКИД", on_click=lambda _: (selected_image_paths.clear(), images_row.controls.clear(), page.update()))]),
        images_row, object_dropdown, ft.Row([temp_input, inspector_comment]),
        ft.ElevatedButton("🔍 ОБСТЕЖЕННЯ", on_click=perform_analysis, width=350, bgcolor=ft.colors.BLUE_900, color="white"),
        risk_indicator, ft.Divider(), ai_response_text,
        ft.ElevatedButton("📄 ЗБЕРЕГТИ АКТ", icon=ft.icons.SAVE, on_click=save_act, width=350, bgcolor="green", color="white")
    )

ft.app(target=main)
