import flet as ft
import traceback
import urllib.request
import urllib.error
import base64
import json
import os
import datetime

def main(page: ft.Page):
    # Базові налаштування сторінки
    page.title = "VET-INSPECTOR AUDIT PRO"
    page.padding = 15 
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # 1. ЕКРАН ЗАВАНТАЖЕННЯ (Щоб не було білого екрана)
    loading_text = ft.Text("⏳ Завантаження інтерфейсу...", size=18, color=ft.colors.BLUE_900, weight=ft.FontWeight.BOLD)
    page.add(ft.Container(content=loading_text, alignment=ft.alignment.center, padding=50))
    page.update()

    try:
        # 1. ВСТАВТЕ СЮДИ ВАШ БАЗОВИЙ API КЛЮЧ
        DEFAULT_API_KEY = "AIzaSyCoi5-6zcMFWW6aB5Gul6dPm5i1frn_EFI"

        # 2. СИСТЕМНИЙ ПРОМПТ
        system_instruction = """
        Ти — провідний ветеринарно-санітарний інспектор-аналітик України. 
        Твоя спеціалізація — контроль безпечності харчових продуктів.
        База знань: Накази №16, №46, №28, №57, №1032, Закони №1870-IV, №771, КУпАП (ст. 107, 160).
        ПРАВИЛО ПРІОРИТЕТУ: Якщо людина-інспектор передає коментар "Недоліків немає" або подібний, 
        ти ПОВИНЕН погодитися з ним, встановити ЗЕЛЕНИЙ рівень ризику і не шукати порушень.
        ОБОВ'ЯЗКОВИЙ АНАЛІЗ: Завжди оцінюй гігієну продавців, стан місця для продажу, чистоту поверхонь, стан ножів/інвентарю та наявність рукавичок.
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
            content=ft.Column([
                ft.Text("Якщо базовий ключ не працює, введіть новий нижче:"),
                api_key_input
            ], tight=True),
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
            ft.Text("VET-INSPECTOR PRO", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900, expand=True),
            ft.IconButton(icon=ft.icons.SETTINGS, on_click=open_settings, tooltip="Налаштування API")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        images_row = ft.Row(wrap=True, spacing=10, alignment=ft.MainAxisAlignment.START)
        
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
        
        temp_input = ft.TextField(label="T °C", expand=1)
        inspector_comment = ft.TextField(label="Висновок інспектора", hint_text="Коментар...", expand=2)
        inputs_row = ft.Row([temp_input, inspector_comment])
        
        risk_indicator = ft.Container(
            content=ft.Text("РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.colors.GREY, padding=10, border_radius=5, alignment=ft.alignment.center
        )
        
        ai_response_text = ft.Markdown(value="*Очікування об'єкта...*", selectable=True, extension_set="gitHubWeb")

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
                
                prompt = f"Проаналізуй усі надані фото в комплексі.\nДані від інспектора:\n- Об'єкт: {object_dropdown.value}\n- Температура: {temp_input.value} °C\n- ВИСНОВОК ІНСПЕКТОРА: {inspector_comment.value}\n\nТвоє завдання:\n1. Визнач рівень ризику тегом: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ] або [РИЗИК_ЧЕРВОНИЙ].\n2. Опиши виявлені порушення з посиланням на пункти законодавства.\n3. Зазнач можливі штрафи та алгоритм дій."

                parts = [{"text": prompt}]
                for path in selected_image_paths:
                    with open(path, "rb") as img_file:
                        b64_data = base64.b64encode(img_file.read()).decode("utf-8")
                        parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_data
                            }
                        })

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
                     ai_response_text.value = f"❌ Помилка API або сервера (Код: {http_err.code}). Перевірте ключ у Налаштуваннях (⚙️)."
                     
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
                if not os.path.exists(save_dir):
                    save_dir = os.getcwd()
            except:
                save_dir = os.getcwd()
                
            filepath = os.path.join(save_dir, filename)
            
            images_html = ""
            for path in selected_image_paths:
                try:
                    with open(path, "rb") as img_file:
                        b64_str = base64.b64encode(img_file.read()).decode('utf-8')
                        images_html += f"<img src='data:image/jpeg;base64,{b64_str}' style='max-width: 100%; height: auto; margin: 10px 0; border-radius: 5px;'><br>"
                except:
                    pass

            html_content = f"<html><body><h1>АКТ ОБСТЕЖЕННЯ</h1><p><b>Дата:</b> {current_time}</p><div>{images_html}</div><pre>{ai_response_text.value}</pre></body></html>"
            
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(html_content)
                ai_response_text.value += f"\n\n---\n**✅ АКТ ЗБЕРЕЖЕНО В ПАПКУ DOWNLOADS!**"
            except Exception as ex:
                ai_response_text.value += f"\n\n---\n**❌ Помилка збереження:** {ex}"
                
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

        # 2. ОЧИЩАЄМО ЕКРАН ВІД "ЗАВАНТАЖЕННЯ" І МАЛЮЄМО ІНТЕРФЕЙС
        page.controls.clear()
        page.add(
            ft.Column([
                title_row,
                ft.Row([ft.ElevatedButton("📷 ДОДАТИ ФОТО", icon=ft.icons.CAMERA_ALT, on_click=lambda _: file_picker.pick_files(allow_multiple=True), expand=True)]),
                images_row,
                object_dropdown,
                inputs_row,
                ft.ElevatedButton("🔍 ПРОВЕСТИ ОБСТЕЖЕННЯ", icon=ft.icons.GAVEL, on_click=perform_analysis, bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE),
                risk_indicator,
                ft.Divider(),
                ai_response_text,
                ft.Divider(),
                ft.Row([ft.ElevatedButton("🔄 НОВЕ ОБСТЕЖЕННЯ", icon=ft.icons.REFRESH, on_click=reset_form, color=ft.colors.RED_700, expand=True)]),
                ft.ElevatedButton("📄 СКЛАСТИ АКТ", icon=ft.icons.SAVE, on_click=generate_act, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
            ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        page.update()

    except Exception as critical_error:
        page.controls.clear()
        page.add(
            ft.Text("🚨 ПОМИЛКА ПРИ ЗАПУСКУ ДОДАТКА", color=ft.colors.RED, size=20, weight=ft.FontWeight.BOLD),
            ft.TextField(value=traceback.format_exc(), multiline=True, read_only=True, color=ft.colors.RED_900, text_size=12, min_lines=20)
        )
        page.update()

ft.app(target=main)
