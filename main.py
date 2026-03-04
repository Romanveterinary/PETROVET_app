import flet as ft
import traceback
import urllib.request
import urllib.error
import base64
import json
import os
import datetime

def main(page: ft.Page):
    # Мобільні налаштування екрана
    page.title = "VET-INSPECTOR"
    page.padding = 20 
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    
    try:
        # 1. ВСТАВТЕ СЮДИ ВАШ БАЗОВИЙ API КЛЮЧ
        DEFAULT_API_KEY = "AIzaSyCoi5-6zcMFWW6aB5Gul6dPm5i1frn_EFI"

        system_instruction = """
        Ти — провідний ветеринарно-санітарний інспектор-аналітик України. 
        Твоя спеціалізація — контроль безпечності харчових продуктів.
        База знань: Накази №16, №46, №28, №57, №1032, Закони №1870-IV, №771, КУпАП.
        ПРАВИЛО ПРІОРИТЕТУ: Якщо інспектор пише "Недоліків немає", ти погоджуєшся і ставиш ЗЕЛЕНИЙ ризик.
        """

        selected_image_paths = []
        
        api_key_input = ft.TextField(label="Новий Gemini API Key", password=True, can_reveal_password=True)
        
        def save_api_key(e):
            page.client_storage.set("GEMINI_API_KEY", api_key_input.value)
            settings_dialog.open = False
            page.snack_bar = ft.SnackBar(ft.Text("✅ Новий API Ключ збережено!"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()

        settings_dialog = ft.AlertDialog(
            title=ft.Text("Налаштування API"),
            content=api_key_input,
            actions=[ft.TextButton("Зберегти", on_click=save_api_key)]
        )
        page.overlay.append(settings_dialog)

        def open_settings(e):
            saved_key = page.client_storage.get("GEMINI_API_KEY")
            if saved_key:
                api_key_input.value = saved_key
            settings_dialog.open = True
            page.update()

        title_row = ft.Row([
            ft.Text("VET-INSPECTOR PRO", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.IconButton(icon=ft.icons.SETTINGS, on_click=open_settings)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        images_row = ft.Row(wrap=True, spacing=10)
        
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
        
        # Поля тепер одне під одним для безпеки малювання на мобільному
        temp_input = ft.TextField(label="Температура °C")
        inspector_comment = ft.TextField(label="Висновок інспектора", multiline=True)
        
        risk_indicator = ft.Container(
            content=ft.Text("РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.colors.GREY, padding=10, border_radius=5, alignment=ft.alignment.center
        )
        
        # Прибрано розширення gitHubWeb, яке "ламає" Android
        ai_response_text = ft.Markdown(value="*Очікування об'єкта...*", selectable=True)

        def pick_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                for f in e.files:
                    selected_image_paths.append(f.path)
                    images_row.controls.append(
                        ft.Image(src=f.path, width=80, height=80, fit=ft.ImageFit.COVER, border_radius=5)
                    )
                page.update()

        file_picker = ft.FilePicker(on_result=pick_file_result)
        page.overlay.append(file_picker)

        def perform_analysis(e):
            if "пиво будеш" in inspector_comment.value.lower():
                ai_response_text.value = "## БЕЗ РОМАНА ВАСИЛЬОВИЧА НІ ! 🍻"
                risk_indicator.bgcolor = ft.colors.BLUE
                risk_indicator.content.value = "РЕЖИМ ВІДПОЧИНКУ"
                page.update()
                return

            if not selected_image_paths:
                ai_response_text.value = "❌ Будь ласка, додайте хоча б одне фото для аналізу."
                page.update()
                return
                
            ai_response_text.value = "⏳ *Збираю дані та формую юридичне обґрунтування...*"
            page.update()

            try:
                current_key = page.client_storage.get("GEMINI_API_KEY")
                if not current_key:
                    current_key = DEFAULT_API_KEY

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={current_key}"
                
                prompt = f"Проаналізуй фото.\nОб'єкт: {object_dropdown.value}\nТемпература: {temp_input.value} °C\nВИСНОВОК ІНСПЕКТОРА: {inspector_comment.value}\n\n1. Визнач рівень ризику: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ] або [РИЗИК_ЧЕРВОНИЙ].\n2. Опиши порушення та законодавство."

                parts = [{"text": prompt}]
                for path in selected_image_paths:
                    with open(path, "rb") as img_file:
                        b64_data = base64.b64encode(img_file.read()).decode("utf-8")
                        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_data}})

                payload = {
                    "system_instruction": {"parts": [{"text": system_instruction}]},
                    "contents": [{"parts": parts}]
                }

                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                
                try:
                    with urllib.request.urlopen(req) as response:
                        result_data = json.loads(response.read().decode('utf-8'))
                        result_text = result_data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        if "[РИЗИК_ЗЕЛЕНИЙ]" in result_text:
                            risk_indicator.bgcolor = ft.colors.GREEN
                            risk_indicator.content.value = "РІВЕНЬ РИЗИКУ: ЗЕЛЕНИЙ"
                        elif "[РИЗИК_ЖОВТИЙ]" in result_text:
                            risk_indicator.bgcolor = ft.colors.YELLOW_800
                            risk_indicator.content.value = "РІВЕНЬ РИЗИКУ: ЖОВТИЙ"
                        elif "[РИЗИК_ЧЕРВОНИЙ]" in result_text:
                            risk_indicator.bgcolor = ft.colors.RED
                            risk_indicator.content.value = "РІВЕНЬ РИЗИКУ: ЧЕРВОНИЙ"

                        result_text = result_text.replace("[РИЗИК_ЗЕЛЕНИЙ]", "").replace("[РИЗИК_ЖОВТИЙ]", "").replace("[РИЗИК_ЧЕРВОНИЙ]", "")
                        ai_response_text.value = result_text.strip()
                except urllib.error.HTTPError as http_err:
                     ai_response_text.value = f"❌ Помилка API. Перевірте ключ у Налаштуваннях (⚙️)."
                     
                page.update()
                
            except Exception as ex:
                ai_response_text.value = f"❌ Системна помилка: {str(ex)}"
                page.update()

        def generate_act(e):
            if "Очікування" in ai_response_text.value or not ai_response_text.value:
                return
            current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"AKT_{current_time}.html"
            try:
                save_dir = "/storage/emulated/0/Download"
                if not os.path.exists(save_dir): save_dir = os.getcwd()
            except: save_dir = os.getcwd()
            filepath = os.path.join(save_dir, filename)
            
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(f"<html><body><h1>АКТ</h1><pre>{ai_response_text.value}</pre></body></html>")
                ai_response_text.value += f"\n\n**✅ АКТ ЗБЕРЕЖЕНО В ЗАВАНТАЖЕННЯХ!**"
            except Exception as ex:
                ai_response_text.value += f"\n\n**❌ Помилка збереження:** {ex}"
            page.update()

        def reset_form(e):
            selected_image_paths.clear()
            images_row.controls.clear()
            temp_input.value = ""
            inspector_comment.value = ""
            object_dropdown.value = None
            ai_response_text.value = "*Очікування об'єкта...*"
            risk_indicator.bgcolor = ft.colors.GREY
            risk_indicator.content.value = "РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО"
            page.update()

        # Виводимо всі елементи на екран у вигляді "стовпчика"
        page.add(
            ft.Column([
                title_row,
                ft.ElevatedButton("📷 ДОДАТИ ФОТО", icon=ft.icons.CAMERA_ALT, on_click=lambda _: file_picker.pick_files(allow_multiple=True)),
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
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )

    except Exception as critical_error:
        page.add(ft.Text(f"🚨 ПОМИЛКА: {str(critical_error)}", color=ft.colors.RED))

ft.app(target=main)
