import flet as ft
import google.generativeai as genai
import PIL.Image
import os
import datetime
import base64

# Використовуємо тільки безпечну папку для Android
safe_dir = os.environ.get("FLET_APP_STORAGE", ".")
key_path = os.path.join(safe_dir, "gemini_key.txt")
DEFAULT_KEY = "AIzaSyDHd-5YhrPFUk1Mht2Csfkn0-6xQa0dM2E"

system_instruction = "Ти — ветеринарний інспектор України. База: Накази №16, №28, №1032. ПРАВИЛО ПРІОРИТЕТУ: якщо інспектор каже 'Недоліків немає', став ЗЕЛЕНИЙ ризик."

def main(page: ft.Page):
    page.title = "VET-INSPECTOR AUDIT PRO"
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    # window_width/height ВИДАЛЕНО (це причина білого екрана на Android)

    def get_key():
        if os.path.exists(key_path):
            try:
                with open(key_path, "r") as f: return f.read().strip()
            except: pass
        return DEFAULT_KEY

    genai.configure(api_key=get_key())
    selected_image_paths = []
    img_row = ft.Row(wrap=True)

    # --- UI ---
    ai_res = ft.Markdown(value="*Очікування...*", selectable=True)
    risk_box = ft.Container(content=ft.Text("РИЗИК: НЕ ВИЗНАЧЕНО", weight="bold"), bgcolor="grey", padding=10, border_radius=5)

    fp = ft.FilePicker(on_result=lambda e: (
        [selected_image_paths.append(f.path) for f in e.files],
        [img_row.controls.append(ft.Image(src=f.path, width=80, height=80, fit="cover")) for f in e.files],
        page.update()
    ) if e.files else None)
    page.overlay.append(fp)

    def do_audit(e):
        if not selected_image_paths: return
        ai_res.value = "⏳ *Обробка...*"; page.update()
        try:
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
            imgs = [PIL.Image.open(p) for p in selected_image_paths]
            response = model.generate_content(["Оціни ризик: [РИЗИК_ЗЕЛЕНИЙ], [РИЗИК_ЖОВТИЙ], [РИЗИК_ЧЕРВОНИЙ]."] + imgs)
            res = response.text
            if "[РИЗИК_ЗЕЛЕНИЙ]" in res: risk_box.bgcolor = "green"
            elif "[РИЗИК_ЧЕРВОНИЙ]" in res: risk_box.bgcolor = "red"
            ai_res.value = res.replace("[РИЗИК_ЗЕЛЕНИЙ]", "").replace("[РИЗИК_ЧЕРВОНИЙ]", "").strip()
        except Exception as ex: ai_res.value = f"❌ Помилка: {str(ex)}"
        page.update()

    page.add(
        ft.Row([ft.Text("PETROVET 49.0", size=20, weight="bold")]),
        ft.ElevatedButton("📷 ДОДАТИ ФОТО", on_click=lambda _: fp.pick_files(allow_multiple=True)),
        img_row,
        ft.ElevatedButton("🔍 ПРОВЕСТИ ОБСТЕЖЕННЯ", on_click=do_audit, width=350, bgcolor=ft.colors.BLUE_900, color="white"),
        risk_box, ft.Divider(), ai_res
    )

ft.app(target=main)
