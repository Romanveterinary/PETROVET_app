import flet as ft
import urllib.request
import urllib.error
import base64
import json
import os
import datetime

def main(page: ft.Page):
    # 1. МАГІЧНІ НАЛАШТУВАННЯ З ВАШОГО РОБОЧОГО КОДУ
    page.title = "VET-INSPECTOR"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.window_width = 400
    page.window_height = 800
    page.padding = 15

    # 2. БЕЗПЕЧНА ПАПКА АНДРОЇД (Головний секрет!)
    safe_dir = os.environ.get("FLET_APP_STORAGE", ".")
    key_file_path = os.path.join(safe_dir, "api_key.txt")

    # 3. БЕЗПЕЧНЕ ЗБЕРЕЖЕННЯ (ЗАМІСТЬ ГЛЮЧНОГО client_storage)
    DEFAULT_API_KEY = "AIzaSyCoi5-6zcMFWW6aB5Gul6dPm5i1frn_EFI"
    
    def get_saved_key():
        try:
            if os.path.exists(key_file_path):
                with open(key_file_path, "r") as f:
                    return f.read().strip()
        except:
            pass
        return DEFAULT_API_KEY

    system_instruction = "Ти — провідний ветеринарно-санітарний інспектор-аналітик України..."
    selected_image_paths = []
    
    # 4. БЕЗПЕЧНА ГАЛЕРЕЯ (Точно як у вас)
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

    # 5. ІНТЕРФЕЙС
    api_key_input = ft.TextField(label="Новий Gemini API Key", password=True, can_reveal_password=True, value=get_saved_key())
    
    def save_api_key(e):
        try:
            with open(key_file_path, "w") as f:
                f.write(api_key_input.value.strip())
            page.close(settings_dialog)
            page.open(ft.SnackBar(content=ft.Text("✅ Новий API Ключ збережено!"), bgcolor="green"))
        except Exception as ex:
            page.open(ft.SnackBar(content=ft.Text(f"❌ Помилка: {ex}"), bgcolor="red"))

    settings_dialog = ft.AlertDialog(
        title=ft.Text("Налаштування API"),
        content=api_key_input,
        actions=[ft.TextButton("Зберегти", on_click=save_api_key)]
    )

    title_row = ft.Row([
        ft.Text("VET-INSPECTOR PRO", size=20, weight="bold", color=ft.colors.BLUE_900),
        ft.IconButton(icon=ft.icons.SETTINGS, on_click=lambda e: page.open(settings_dialog))
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    object_dropdown = ft.Dropdown(
        label="Об'єкт контролю",
        options=[
            ft.dropdown.Option("М'ясо (туші)"),
            ft.dropdown.Option("Молоко та молочні продукти"),
            ft.dropdown.Option("Риба жива"),
            ft.dropdown.Option("Інші харчові товари"),
            ft.dropdown.Option("Місце торгівлі/Обладнання"),
        ]
    )
    
    temp_input = ft.TextField(label="Температура °C")
    inspector_comment = ft.TextField(label="Висновок інспектора", multiline=True)
    
    risk_indicator = ft.Text("РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО", color=ft.colors.GREY, weight="bold")
    ai_response_text = ft.Text(value="Очікування об'єкта...", selectable=True, size=14)

    def perform_analysis(e):
        if "пиво" in inspector_comment.value.lower():
            ai_response_text.value = "БЕЗ РОМАНА ВАСИЛЬОВИЧА НІ ! 🍻"
            risk_indicator.color = ft.colors.BLUE
            risk_indicator.value = "РЕЖИМ ВІДПОЧИНКУ"
            page.update()
            return

        if not selected_image_paths:
            ai_response_text.value = "❌ Будь ласка, додайте хоча б одне фото."
            page.update()
            return
            
        ai_response_text.value = "⏳ Збираю дані та формую юридичне обґрунтування..."
        page.update()

        try:
            current_key = get_saved_key()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={current_key}"
            prompt = f"Проаналізуй фото.\nОб'єкт: {object_dropdown.value}\nТемпература: {temp_input.value} °C\nВИСНОВОК: {inspector_comment.value}\n\n1. Визнач ризик: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ] або [РИЗИК_ЧЕРВОНИЙ].\n2. Опиши порушення та законодавство."

            parts = [{"text": prompt}]
            for path in selected_image_paths:
                with open(path, "rb") as img_file:
                    b64_data = base64.b64encode(img_file.read()).decode("utf-8")
                    parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_data}})

            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"parts": parts}]
            }

            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                result_data = json.loads(response.read().decode('utf-8'))
                result_text = result_data["candidates"][0]["content"]["parts"][0]["text"]
                
                if "[РИЗИК_ЗЕЛЕНИЙ]" in result_text:
                    risk_indicator.color = ft.colors.GREEN
                    risk_indicator.value = "РІВЕНЬ РИЗИКУ: ЗЕЛЕНИЙ"
                elif "[РИЗИК_ЖОВТИЙ]" in result_text:
                    risk_indicator.color = ft.colors.YELLOW_800
                    risk_indicator.value = "РІВЕНЬ РИЗИКУ: ЖОВТИЙ"
                elif "[РИЗИК_ЧЕРВОНИЙ]" in result_text:
                    risk_indicator.color = ft.colors.RED
                    risk_indicator.value = "РІВЕНЬ РИЗИКУ: ЧЕРВОНИЙ"

                result_text = result_text.replace("[РИЗИК_ЗЕЛЕНИЙ]", "").replace("[РИЗИК_ЖОВТИЙ]", "").replace("[РИЗИК_ЧЕРВОНИЙ]", "")
                ai_response_text.value = result_text.strip()
        except Exception as http_err:
             ai_response_text.value = f"❌ Помилка API: {str(http_err)}"
        page.update()

    def generate_act(e):
        if not ai_response_text.value or "Очікування" in ai_response_text.value: return
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"AKT_{current_time}.html"
        
        # Секретна безпечна папка для актів (як у вашому коді)
        filepath = os.path.join(safe_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(f"<html><body><h1>АКТ</h1><pre>{ai_response_text.value}</pre></body></html>")
            ai_response_text.value += f"\n\n✅ АКТ ЗБЕРЕЖЕНО в пам'яті програми!"
        except Exception as ex:
            ai_response_text.value += f"\n\n❌ Помилка збереження: {ex}"
        page.update()

    def reset_form(e):
        selected_image_paths.clear()
        images_row.controls.clear()
        temp_input.value = ""
        inspector_comment.value = ""
        object_dropdown.value = None
        ai_response_text.value = "Очікування об'єкта..."
        risk_indicator.color = ft.colors.GREY
        risk_indicator.value = "РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО"
        page.update()

    page.add(
        title_row,
        ft.ElevatedButton("📷 ДОДАТИ ФОТО", icon=ft.icons.CAMERA_ALT, on_click=lambda _: fp_photo.pick_files(allow_multiple=True)),
        images_row,
        object_dropdown,
        temp_input,
        inspector_comment,
        ft.ElevatedButton("🔍 ПРОВЕСТИ ОБСТЕЖЕННЯ", icon=ft.icons.GAVEL, on_click=perform_analysis, bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE),
        risk_indicator,
        ft.Divider(),
        ai_response_text,
        ft.Divider(),
        ft.ElevatedButton("🔄 НОВЕ ОБСТЕЖЕННЯ", icon=ft.icons.REFRESH, on_click=reset_form, color=ft.colors.RED_700),
        ft.ElevatedButton("📄 СКЛАСТИ АКТ", icon=ft.icons.SAVE, on_click=generate_act, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
    )

ft.app(target=main)
