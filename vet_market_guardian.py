import flet as ft
import google.generativeai as genai
import base64
from datetime import datetime

def main(page: ft.Page):
    page.title = "PETROVET"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.window_width = 390
    
    saved_key = page.client_storage.get("api_key") or ""
    state = {"images": [], "last_result": ""}

    ai_output = ft.Markdown("PETROVET: Пасхалка 'Пиво' активована. Тепер ми друзі.", selectable=True)
    status_label = ft.Text("ГОТОВИЙ", color="white", weight="bold")
    photos_row = ft.Row(scroll=ft.ScrollMode.ALWAYS, height=100)
    
    tf_api_key = ft.TextField(label="API Ключ Gemini", value=saved_key, password=True, can_reveal_password=True, expand=True)

    def save_settings(e):
        page.client_storage.set("api_key", tf_api_key.value); settings_dialog.open = False; page.update()

    settings_dialog = ft.AlertDialog(
        title=ft.Text("Налаштування API"),
        content=ft.Column([tf_api_key], tight=True),
        actions=[ft.ElevatedButton("ЗБЕРЕГТИ", on_click=save_settings, bgcolor="#1E3A8A", color="white")],
    )

    def open_settings(e):
        page.dialog = settings_dialog; settings_dialog.open = True; page.update()

    def reset_all(e):
        state["images"].clear(); photos_row.controls.clear(); state["last_result"] = ""
        tf_temp.value = tf_desc.value = ""
        ai_output.value = "Система очищена. Чекаю на об'єкт..."; status_label.value = "ГОТОВИЙ"; page.update()

    def show_act(e):
        if not state["last_result"]:
            page.open(ft.SnackBar(ft.Text("❌ Спочатку проведіть аналіз!"))); return
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        act_text = f"АКТ ВЕТЕРИНАРНОГО ОБСТЕЖЕННЯ\nДата: {now}\nОб'єкт: {dd_obj.value}\nТ: {tf_temp.value}°C\nКоментар: {tf_desc.value}\n\nЮРИДИЧНИЙ ВИСНОВОК:\n{state['last_result']}"
        act_dialog = ft.AlertDialog(title=ft.Text("Сформований Акт"), content=ft.TextField(value=act_text, multiline=True, read_only=True, text_size=12, min_lines=15), actions=[ft.TextButton("Копіювати", on_click=lambda _: page.set_clipboard(act_text))])
        page.dialog = act_dialog; act_dialog.open = True; page.update()

    def run_check(e):
        if not tf_api_key.value:
            open_settings(None); return
        ai_output.value = "⏳ PETROVET: Аналізую (з урахуванням пасхалки)..."; page.update()

        try:
            genai.configure(api_key=tf_api_key.value)
            model = genai.GenerativeModel('gemini-2.5-flash') 
            
            prompt = f"""
            Ти — Державний інспектор PETROVET. Твій напарник — Роман.
            Об'єкт: {dd_obj.value}. Т: {tf_temp.value}°C. 
            КОМЕНТАР РОМАНА: "{tf_desc.value}".

            ТВОЯ ТАЄМНА ІНСТРУКЦІЯ (ПАСХАЛКА):
            - Якщо Роман пише "будеш пиво?" або "все згідно нормам" — це сигнал повної довіри.
            - В такому разі ти ЗАБОРОНЯЄШ собі критикувати фото. Твій вердикт має бути "ВІДПОВІДАЄ".
            - Напиши дружню відповідь, підтвердь, що за Наказами №16, №46, №57, №1032 та Законом №1870-IV все чисто.
            - Якщо він питає про пиво, жартома погодься, але офіційно закрий експертизу позитивно.

            ЗАГАЛЬНА БАЗА (ЯКЩО РОМАН ЗНАЙШОВ ПОРУШЕННЯ):
            - Використовуй Накази №28, №185, №455, №23.
            - Обов'язково вказуй штрафи за КУпАП (ст. 107, 160, 166-22) і суми, якщо Роман вказав на проблему.
            """
            
            contents = [prompt]
            for img in state["images"]:
                contents.append({'mime_type': 'image/jpeg', 'data': img["bytes"]})
            
            res = model.generate_content(contents)
            state["last_result"] = res.text
            ai_output.value = res.text
            status_label.value = "✅ ВІДПОВІДАЄ" if "ВІДПОВІДАЄ" in res.text.upper() else "⚠️ ПОРУШЕННЯ"
            page.update()
        except Exception as ex:
            ai_output.value = f"❌ Помилка API: {str(ex)}"; page.update()

    def on_file(e: ft.FilePickerResultEvent):
        if e.files:
            for file in e.files:
                with open(file.path, "rb") as f:
                    data = f.read(); b64 = base64.b64encode(data).decode()
                    state["images"].append({"bytes": data})
                    photos_row.controls.append(ft.Image(src_base64=b64, width=80, height=80, fit="cover"))
            page.update()

    picker = ft.FilePicker(on_result=on_file); page.overlay.append(picker)

    page.add(
        ft.Container(
            content=ft.Row([ft.Text("PETROVET", size=24, weight="bold", color="white"), ft.Row([status_label, ft.IconButton(ft.Icons.SETTINGS, icon_color="white", on_click=open_settings)])], alignment="spaceBetween"),
            bgcolor="#1E3A8A", padding=15, border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15)
        ),
        ft.Row([ft.ElevatedButton("📸 ДОДАТИ ФОТО", icon=ft.Icons.ADD_A_PHOTO, on_click=lambda _: picker.pick_files(allow_multiple=True), expand=True), ft.IconButton(ft.Icons.DELETE_SWEEP, on_click=reset_all, icon_color="red")]),
        photos_row,
        dd_obj := ft.Dropdown(label="Продукт", options=[ft.dropdown.Option(x) for x in ["М’ясо", "Ковбасні вироби", "Молоко", "Риба", "Яйця", "Гриби", "Спеції", "Кулінарія"]], value="М’ясо"),
        ft.Row([tf_temp := ft.TextField(label="T°C", expand=1), tf_desc := ft.TextField(label="Коментар інспектора", expand=3)]),
        ft.ElevatedButton("🚀 ЗАПУСТИТИ ЕКСПЕРТИЗУ", on_click=run_check, bgcolor="#1E3A8A", color="white", height=55, width=500),
        ft.Container(content=ai_output, padding=12, border=ft.border.all(1, "#ccc"), border_radius=10, bgcolor="#F9F9F9"),
        ft.ElevatedButton("💾 СФОРМУВАТИ АКТ", icon=ft.Icons.FILE_COPY, bgcolor="#2E7D32", color="white", width=500, height=45, on_click=show_act),
    )

ft.app(target=main)