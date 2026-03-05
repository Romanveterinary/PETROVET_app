import flet as ft
import os
import google.generativeai as genai

def main(page: ft.Page):
    # Налаштування з вашого робочого VetAI Pro
    page.title = "VET-INSPECTOR"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.window_width = 400
    page.window_height = 800
    page.padding = 15

    # Безпечна папка для Андроїда
    safe_dir = os.environ.get("FLET_APP_STORAGE", ".")
    key_file_path = os.path.join(safe_dir, "api_key.txt")
    DEFAULT_API_KEY = "ВАШ_БАЗОВИЙ_КЛЮЧ"
    
    def get_saved_key():
        try:
            if os.path.exists(key_file_path):
                with open(key_file_path, "r") as f:
                    return f.read().strip()
        except: pass
        return DEFAULT_API_KEY

    system_instruction = "Ти — провідний ветеринарно-санітарний інспектор-аналітик."
    selected_image_paths = []
    
    images_row = ft.Row(wrap=True, spacing=10)
    fp_photo = ft.FilePicker()
    
    def pick_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                selected_image_paths.append(f.path)
                images_row.controls.append(ft.Image(src=f.path, width=80, height=80, fit=ft.ImageFit.COVER, border_radius=5))
            page.update()
            
    fp_photo.on_result = pick_file_result
    page.overlay.append(fp_photo)

    api_key_input = ft.TextField(label="Gemini API Key", password=True, can_reveal_password=True, value=get_saved_key())
    
    def save_api_key(e):
        try:
            with open(key_file_path, "w") as f:
                f.write(api_key_input.value.strip())
            page.close(settings_dialog)
            page.open(ft.SnackBar(content=ft.Text("✅ Ключ збережено!"), bgcolor="green"))
        except Exception as ex:
            pass

    settings_dialog = ft.AlertDialog(
        title=ft.Text("Налаштування API"),
        content=api_key_input,
        actions=[ft.TextButton("Зберегти", on_click=save_api_key)]
    )

    title_row = ft.Row([
        ft.Text("VET-INSPECTOR", size=20, weight="bold", color=ft.colors.BLUE_900),
        ft.IconButton(icon=ft.icons.SETTINGS, on_click=lambda e: page.open(settings_dialog))
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    object_dropdown = ft.Dropdown(
        label="Об'єкт контролю",
        options=[ft.dropdown.Option("М'ясо (туші)"), ft.dropdown.Option("Місце торгівлі")],
        value="М'ясо (туші)"
    )
    
    temp_input = ft.TextField(label="Температура °C", value="38.0")
    inspector_comment = ft.TextField(label="Висновок інспектора", multiline=True)
    
    risk_indicator = ft.Text("РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО", color=ft.colors.GREY, weight="bold")
    ai_response_text = ft.Text(value="Очікування об'єкта...", selectable=True, size=14)

    def perform_analysis(e):
        if not selected_image_paths:
            ai_response_text.value = "❌ Додайте фото."
            page.update()
            return
            
        ai_response_text.value = "⏳ Аналіз даних..."
        page.update()

        try:
            # Використовуємо бібліотеку genai, як у вашому VetAI
            genai.configure(api_key=get_saved_key())
            model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_instruction)
            
            prompt = f"Об'єкт: {object_dropdown.value}\nТемпература: {temp_input.value}\nВисновок: {inspector_comment.value}\nВизнач ризик: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ] або [РИЗИК_ЧЕРВОНИЙ]. Опиши порушення."
            
            contents = []
            for path in selected_image_paths:
                with open(path, "rb") as f:
                    contents.append({'mime_type': 'image/jpeg', 'data': f.read()})
            contents.append(prompt)

            response = model.generate_content(contents)
            result_text = response.text
            
            if "[РИЗИК_ЗЕЛЕНИЙ]" in result_text:
                risk_indicator.color, risk_indicator.value = ft.colors.GREEN, "РІВЕНЬ РИЗИКУ: ЗЕЛЕНИЙ"
            elif "[РИЗИК_ЖОВТИЙ]" in result_text:
                risk_indicator.color, risk_indicator.value = ft.colors.YELLOW_800, "РІВЕНЬ РИЗИКУ: ЖОВТИЙ"
            elif "[РИЗИК_ЧЕРВОНИЙ]" in result_text:
                risk_indicator.color, risk_indicator.value = ft.colors.RED, "РІВЕНЬ РИЗИКУ: ЧЕРВОНИЙ"

            ai_response_text.value = result_text.replace("[РИЗИК_ЗЕЛЕНИЙ]", "").replace("[РИЗИК_ЖОВТИЙ]", "").replace("[РИЗИК_ЧЕРВОНИЙ]", "").strip()
        except Exception as err:
             ai_response_text.value = f"❌ Помилка: {str(err)}"
        page.update()

    def reset_form(e):
        selected_image_paths.clear()
        images_row.controls.clear()
        temp_input.value = inspector_comment.value = ""
        ai_response_text.value = "Очікування об'єкта..."
        risk_indicator.color, risk_indicator.value = ft.colors.GREY, "РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО"
        page.update()

    page.add(
        title_row,
        ft.ElevatedButton("📷 ДОДАТИ ФОТО", icon=ft.icons.CAMERA_ALT, on_click=lambda _: fp_photo.pick_files(allow_multiple=True)),
        images_row, object_dropdown, temp_input, inspector_comment,
        ft.ElevatedButton("🔍 ПРОВЕСТИ ОБСТЕЖЕННЯ", icon=ft.icons.GAVEL, on_click=perform_analysis, bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE),
        risk_indicator, ft.Divider(), ai_response_text, ft.Divider(),
        ft.ElevatedButton("🔄 НОВЕ ОБСТЕЖЕННЯ", icon=ft.icons.REFRESH, on_click=reset_form, color=ft.colors.RED_700)
    )

ft.app(target=main)
