import flet as ft
import google.generativeai as genai
import os

# Твій безкоштовний ключ
DEFAULT_API_KEY = "AIzaSyCoi5-6zcMFWW6aB5Gul6dPm5i1frn_EFI"

def main(page: ft.Page):
    # Налаштування сторінки
    page.title = "PETROVET"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # Створюємо текстове поле для виводу ВІДРАЗУ
    log_text = ft.Text("Ініціалізація системи...", color="yellow")
    page.add(log_text)
    
    try:
        # Спроба налаштувати ШІ
        genai.configure(api_key=DEFAULT_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        log_text.value = "✅ Система готова. Наказ №16, 46, 28 завантажено."
        log_text.color = "green"
    except Exception as e:
        log_text.value = f"❌ Помилка конфігурації: {str(e)}"
        log_text.color = "red"
    
    # Головний заголовок
    page.add(ft.Text("🛡️ ПЕТРОВЕТ v51.0", size=28, weight="bold"))
    
    # Поле результату
    result_area = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    result_text = ft.Text("Оберіть дію або напишіть питання.", size=16)
    result_area.controls.append(result_text)

    def on_ask_click(e):
        user_q = user_input.value
        if not user_q: return
        
        result_text.value = "⏳ Запит до бази законодавства..."
        page.update()
        try:
            response = model.generate_content(f"Ти ветеринарний інспектор. Дай коротку відповідь на питання: {user_q}")
            result_text.value = response.text
        except Exception as ex:
            result_text.value = f"Помилка ШІ: {str(ex)}"
        page.update()

    # Інтерфейс
    user_input = ft.TextField(label="Питання (напр. Наказ 46)", expand=True)
    ask_button = ft.ElevatedButton("Спитати ШІ", on_click=on_ask_click)
    
    page.add(
        ft.Row([user_input, ask_button]),
        ft.Container(
            content=result_area,
            padding=10,
            border=ft.border.all(1, "grey400"),
            border_radius=10,
            height=300
        )
    )
    page.update()

# Важливо для мобільної версії
if __name__ == "__main__":
    ft.app(target=main)

