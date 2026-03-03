import flet as ft
import google.generativeai as genai

def main(page: ft.Page):
    page.title = "PETROVET 49.0"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Захист від білого екрана: спершу просто вітання
    content_area = ft.Column([ft.Text("Завантаження PETROVET...", size=20)])
    page.add(content_area)

    def start_app():
        try:
            # Тут твій основний код логіки з законами
            content_area.controls.clear()
            content_area.controls.append(ft.Text("Вітаю, Романе! Оберіть розділ експертизи:", size=22, weight="bold"))
            # ... (решта кнопок і логіки)
            page.update()
        except Exception as e:
            content_area.controls.add(ft.Text(f"Помилка запуску: {e}", color="red"))
            page.update()

    ft.app(target=main)
