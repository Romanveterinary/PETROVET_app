import flet as ft
import google.generativeai as genai
import PIL.Image
import os
import datetime
import base64

# 1. ВСТАВТЕ СЮДИ ВАШ БАЗОВИЙ (ПЕРШИЙ) API КЛЮЧ
DEFAULT_API_KEY = "AIzaSyCoi5-6zcMFWW6aB5Gul6dPm5i1frn_EFI"

# 2. СИСТЕМНИЙ ПРОМПТ (PETROVET 49.0)
system_instruction = """
Ти — провідний ветеринарно-санітарний інспектор-аналітик України. 
Твоя спеціалізація — контроль безпечності харчових продуктів.
База знань: Накази №16, №46, №28, №57, №1032, Закони №1870-IV, №771, КУпАП (ст. 107, 160).
ПРАВИЛО ПРІОРИТЕТУ: Якщо людина-інспектор передає коментар "Недоліків немає" або подібний, 
ти ПОВИНЕН погодитися з ним, встановити ЗЕЛЕНИЙ рівень ризику і не шукати порушень.

ОБОВ'ЯЗКОВИЙ АНАЛІЗ: 
Завжди оцінюй гігієну продавців, стан місця для продажу, чистоту поверхонь, стан ножів/інвентарю та наявність рукавичок. 
Описуй порушення по пунктах із суворим посиланням на відповідне законодавство (наприклад, Наказ №16).
"""

def main(page: ft.Page):
    page.title = "VET-INSPECTOR AUDIT PRO"
    # Для мобільного прибираємо жорстку ширину вікна, додаємо адаптивні відступи
    page.padding = 15 
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- ЗМІННІ СТАНУ ---
    selected_image_paths = []
    
    # --- НАЛАШТУВАННЯ API КЛЮЧА ---
    api_key_input = ft.TextField(label="Новий Gemini API Key", password=True, can_reveal_password=True)
    
    def save_api_key(e):
        page.client_storage.set("GEMINI_API_KEY", api_key_input.value)
        genai.configure(api_key=api_key_input.value)
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

    # --- ЛОГІКА ІНІЦІАЛІЗАЦІЇ КЛЮЧА ПРИ СТАРТІ ---
    saved_api_key = page.client_storage.get("GEMINI_API_KEY")
    if saved_api_key:
        genai.configure(api_key=saved_api_key)
    else:
        genai.configure(api_key=DEFAULT_API_KEY)

    # --- ЕЛЕМЕНТИ ІНТЕРФЕЙСУ ---
    title_row = ft.Row([
        ft.Text("VET-INSPECTOR PRO", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900, expand=True),
        ft.IconButton(icon=ft.icons.SETTINGS, on_click=open_settings, tooltip="Налаштування API")
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    # Контейнер для фото, який буде переносити їх на новий рядок, якщо вони не влазять
    images_row = ft.Row(wrap=True, spacing=10, alignment=ft.MainAxisAlignment.START)
    
    # Елементи інтерфейсу (без жорстко заданої ширини)
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
    
    # Використовуємо expand, щоб вони ділили екран: 1 частина під температуру, 2 під коментар
    temp_input = ft.TextField(label="T °C", expand=1)
    inspector_comment = ft.TextField(label="Висновок інспектора", hint_text="Коментар...", expand=2)
    inputs_row = ft.Row([temp_input, inspector_comment])
    
    risk_indicator = ft.Container(
        content=ft.Text("РІВЕНЬ РИЗИКУ: НЕ ВИЗНАЧЕНО", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        bgcolor=ft.colors.GREY, padding=10, border_radius=5, alignment=ft.alignment.center
    )
    
    ai_response_text = ft.Markdown(value="*Очікування об'єкта...*", selectable=True, extension_set="gitHubWeb")

    # --- ФУНКЦІЇ ---
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
            model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)
            pil_images = [PIL.Image.open(path) for path in selected_image_paths]
            
            prompt = f"""
            Проаналізуй усі надані фото в комплексі. 
            Дані від інспектора:
            - Об'єкт: {object_dropdown.value}
            - Температура: {temp_input.value} °C
            - ВИСНОВОК ІНСПЕКТОРА: {inspector_comment.value}
            
            Твоє завдання:
            1. Визнач рівень ризику тегом: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ] або [РИЗИК_ЧЕРВОНИЙ].
            2. Опиши виявлені порушення (гігієна, чистота, ножі, рукавички тощо) з посиланням на пункти законодавства.
            3. Зазнач можливі штрафи та алгоритм дій.
            """
            
            response = model.generate_content([prompt] + pil_images)
            result_text = response.text
            
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
            page.update()
            
        except Exception as ex:
            if "API_KEY_INVALID" in str(ex) or "403" in str(ex) or "400" in str(ex):
                 ai_response_text.value = "❌ Помилка API Ключа. Можливо він заблокований або недійсний. Вставте новий ключ у Налаштуваннях (⚙️)."
            else:
                 ai_response_text.value = f"❌ Помилка аналізу: {str(ex)}"
            page.update()

    def generate_act(e):
        if "Очікування" in ai_response_text.value or not ai_response_text.value:
            return
            
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"AKT_{current_time}.html"
        current_dir = os.getcwd()
        filepath = os.path.join(current_dir, filename)
        
        images_html = ""
        for path in selected_image_paths:
            try:
                with open(path, "rb") as img_file:
                    b64_str = base64.b64encode(img_file.read()).decode('utf-8')
                    images_html += f"<img src='data:image/jpeg;base64,{b64_str}' style='max-width: 100%; height: auto; margin: 10px 0; border-radius: 5px;'><br>"
            except:
                pass

        html_content = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Акт Обстеження</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 15px; max-width: 800px; margin: auto; }}
                h1 {{ color: #0d47a1; text-align: center; border-bottom: 2px solid #0d47a1; padding-bottom: 10px; font-size: 20px; }}
                .info-block {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 14px; }}
                .ai-text {{ white-space: pre-wrap; line-height: 1.6; font-size: 14px; }}
                .photos {{ text-align: center; }}
            </style>
        </head>
        <body>
            <h1>АКТ ВЕТЕРИНАРНО-САНІТАРНОГО ОБСТЕЖЕННЯ</h1>
            <div class="info-block">
                <p><strong>Дата:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Об'єкт:</strong> {object_dropdown.value}</p>
                <p><strong>Температура:</strong> {temp_input.value} °C</p>
                <p><strong>Висновок інспектора:</strong> {inspector_comment.value}</p>
                <p><strong>{risk_indicator.content.value}</strong></p>
            </div>
            <h2>Зафіксовані фотоматеріали:</h2>
            <div class="photos">{images_html}</div>
            <h2>Юридичний висновок (ШІ PETROVET 49.0):</h2>
            <div class="ai-text">{ai_response_text.value}</div>
        </body>
        </html>
        """
        
        try:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(html_content)
            ai_response_text.value += f"\n\n---\n**✅ АКТ ЗБЕРЕЖЕНО!**\nФайл: `{filename}`"
        except Exception as e:
            ai_response_text.value += f"\n\n---\n**❌ Помилка збереження акту:** {e}"
            
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

    # --- КОМПОНУВАННЯ СТОРІНКИ (АДАПТИВНЕ) ---
    page.add(
        ft.Column([
            title_row,
            ft.Row([
                ft.ElevatedButton("📷 ДОДАТИ ФОТО", icon=ft.icons.CAMERA_ALT, on_click=lambda _: file_picker.pick_files(allow_multiple=True), expand=True),
            ]),
            images_row,
            object_dropdown,
            inputs_row,
            ft.ElevatedButton("🔍 ПРОВЕСТИ ОБСТЕЖЕННЯ", icon=ft.icons.GAVEL, on_click=perform_analysis, bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE),
            risk_indicator,
            ft.Divider(),
            ai_response_text,
            ft.Divider(),
            ft.Row([
                 ft.ElevatedButton("🔄 НОВЕ ОБСТЕЖЕННЯ", icon=ft.icons.REFRESH, on_click=reset_form, color=ft.colors.RED_700, expand=True),
            ]),
            ft.ElevatedButton("📄 СКЛАСТИ АКТ", icon=ft.icons.SAVE, on_click=generate_act, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
            # Головний секрет тут: CrossAxisAlignment.STRETCH змушує всі елементи розтягуватися на ширину екрана!
        ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    )

ft.app(target=main)
