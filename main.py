import flet as ft
import google.generativeai as genai

# ВСТАВ СВІЙ API КЛЮЧ
MY_API_KEY = "AIzaSyCoi5-6zcMFWW6aB5Gul6dPm5i1frn_EFI"

def main(page: ft.Page):
    page.title = "PETROVET 49.0"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # Налаштування моделі за твоїм запитом
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except:
        model = None

    # Промпт із твоєю законодавчою базою (11 пунктів)
    LAW_PROMPT = """
    Ти — вет-сан інспектор України. Твої норми:
    1. Наказ №16 (Ринки). 2. Наказ №46 (М'ясо). 3. Наказ №28 (Молоко). 
    4. Наказ №57 (Риба). 5. Наказ №1032 (Документи). 6. Закон №1870-IV. 
    7. Закон №771. 8. КУпАП 107/160. 9. Наказ №23 (Жива риба). 
    10. ДСТУ проб. 11. Норми ЄС.
    """

    header = ft.Text("🛡️ ПЕТРОВЕТ", size=26, weight="bold")
    output = ft.Text("Оберіть категорію:", selectable=True)

    def ask(q):
        if not model:
            output.value = "Помилка ключа"
            page.update()
            return
        output.value = "⏳ Пошук у базі..."
        page.update()
        try:
            res = model.generate_content(f"{LAW_PROMPT}\nПитання: {q}")
            output.value = res.text
        except Exception as e:
            output.value = f"Помилка: {e}"
        page.update()

    # Твій інтерфейс
    page.add(
        header,
        ft.Divider(),
        ft.ElevatedButton("М'ясо (46)", on_click=lambda _: ask("Вимоги Наказу 46 до клеймування")),
        ft.ElevatedButton("Молоко (28)", on_click=lambda _: ask("Вимоги Наказу 28 щодо ПЕТ-тари")),
        ft.ElevatedButton("Штрафи (КУпАП)", on_click=lambda _: ask("Штрафи за статтями 107 та 160")),
        ft.Container(output, padding=10, border=ft.border.all(1, "grey")),
        ft.Row([
            ft.TextField(label="Ваше питання", expand=True, id="user_q"),
            ft.IconButton(icon=ft.icons.SEND, on_click=lambda e: ask(page.get_control("user_q").value))
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)
