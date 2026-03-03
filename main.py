import flet as ft
import google.generativeai as genai

# ВСТАВ СВІЙ БЕЗКОШТОВНИЙ КЛЮЧ ТУТ
MY_API_KEY = "ВСТАВ_ТВІЙ_КЛЮЧ"

def main(page: ft.Page):
    page.title = "PETROVET 49.0"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # Налаштування моделі Gemini 2.5 Flash
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except:
        model = None

    # БАЗА ЗНАНЬ (Твої 11 законів)
    LAW_BASE = """
    Ти — професійний ветеринарний інспектор-аналітик України. 
    Твої відповіді базуються ВИКЛЮЧНО на цих нормах:
    1. Наказ №16 (Вет-сан експертиза на ринках).
    2. Наказ №46 (М'ясо, клеймування, огляд туш та голів).
    3. Наказ №28 (Молоко та молочні продукти, заборона ПЕТ-тари).
    4. Наказ №57 (Риба та рибопродукти).
    5. Наказ №1032 (Протоколи, акти та документація).
    6. Закон №1870-IV (Про ветеринарну медицину).
    7. Закон №771 (Про безпечність та якість харчових продуктів).
    8. КУпАП статті 107 та 160 (Штрафи, стихійна торгівля).
    9. Наказ №23 (Правила реалізації живої риби на ринках).
    10. ДСТУ (Правила відбору проб для експертизи).
    11. Ветеринарно-санітарні вимоги ЄС (для порівняння).
    """

    header = ft.Text("🛡️ ПЕТРОВЕТ: Ветеринарний Контроль", size=26, weight="bold", color="blue400")
    output = ft.Markdown(value="Система готова. Оберіть категорію перевірки:", selectable=True)

    def ask_ai(user_question):
        if not model:
            output.value = "❌ Помилка: Ключ не знайдено або модель недоступна."
            page.update()
            return
        
        output.value = "⏳ Аналізую законодавчу базу (Накази №16, 46, 28...)..."
        page.update()
        
        try:
            full_prompt = f"{LAW_BASE}\n\nПИТАННЯ: {user_question}\n\nВідповідай професійно, з посиланням на статтю або пункт Наказу."
            response = model.generate_content(full_prompt)
            output.value = response.text
        except Exception as e:
            output.value = f"❌ Помилка запиту: {str(e)}"
        page.update()

    # Кнопки швидкого доступу до бази
    btns = ft.Column([
        ft.Row([
            ft.ElevatedButton("М'ясо (Наказ 46)", on_click=lambda _: ask_ai("Які вимоги до клеймування м'яса та огляду голів?"), expand=True),
            ft.ElevatedButton("Молоко (Наказ 28)", on_click=lambda _: ask_ai("Чи дозволена ПЕТ-тара та які норми чистоти молока?"), expand=True),
        ]),
        ft.Row([
            ft.ElevatedButton("Риба (Наказ 23)", on_click=lambda _: ask_ai("Які правила реалізації живої риби на ринках?"), expand=True),
            ft.ElevatedButton("Штрафи (КУпАП)", on_click=lambda _: ask_ai("Які штрафи за статтями 107 та 160 КУпАП?"), expand=True),
        ])
    ])

    user_input = ft.TextField(label="Напишіть своє питання інспектору...", expand=True)
    send_btn = ft.FloatingActionButton(icon=ft.icons.SEND, on_click=lambda _: ask_ai(user_input.value))

    page.add(
        header,
        ft.Divider(),
        btns,
        ft.Container(output, padding=10, border=ft.border.all(1, "grey"), border_radius=10, bgcolor=ft.colors.BLACK12),
        ft.Row([user_input, send_btn])
    )

if __name__ == "__main__":
    ft.app(target=main)
