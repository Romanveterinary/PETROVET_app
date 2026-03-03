import flet as ft
import google.generativeai as genai

# ВСТАВ СВІЙ БЕЗКОШТОВНИЙ КЛЮЧ ТУТ
DEFAULT_API_KEY = "AIzaSyCoi5-6zcMFWW6aB5Gul6dPm5i1frn_EFI"

def main(page: ft.Page):
    page.title = "PETROVET 49.0 — Цифровий Інспектор"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # Стан ключа (можна змінити в процесі роботи)
    current_key = page.client_storage.get("api_key") or DEFAULT_API_KEY

    def configure_ai(key):
        try:
            genai.configure(api_key=key)
            return genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            return None

    model = configure_ai(current_key)

    # Заголовок
    header = ft.Column([
        ft.Text("🛡️ ПЕТРОВЕТ v49.0", size=32, weight="bold", color="blue400"),
        ft.Text("Ветеринарно-санітарна експертиза (Україна)", size=16, italic=True),
        ft.Divider()
    ])

    # Поле виводу результату
    chat_display = ft.Markdown(
        value="**Вітаю, колего!** Оберіть категорію для перевірки або задайте питання ШІ.",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )

    def ask_ai(prompt):
        if not model:
            chat_display.value = "❌ Помилка: ШІ не налаштовано. Перевірте ключ."
            page.update()
            return
        
        chat_display.value = "⏳ Аналізую законодавство... (Наказ №16, №46, №28...)"
        page.update()
        
        try:
            full_prompt = f"Ти — експерт вет-сан експертизи в Україні. Спирайся на 11 основних законів (Накази 16, 46, 28, 57, 1032, Закони 1870-IV, 771 та КУпАП). Питання: {prompt}"
            response = model.generate_content(full_prompt)
            chat_display.value = response.text
        except Exception as e:
            chat_display.value = f"❌ Помилка запиту: {str(e)}"
        page.update()

    # Кнопки швидких перевірок (Твої 11 законів)
    def fast_check(e):
        category = e.control.text
        prompts = {
            "М'ясо (Клейма)": "Які вимоги до клеймування м'яса згідно з Наказом №46?",
            "Молоко (ПЕТ-тара)": "Чи дозволено продаж молока у ПЕТ-тарі згідно із Законом №1870-IV?",
            "Риба (Експертиза)": "Які вимоги Наказу №23 до реалізації живої риби?",
            "Штрафи (КУпАП)": "Які штрафи передбачені статтями 107 та 160 КУпАП на ринках?"
        }
        ask_ai(prompts.get(category, "Розкажи про вет-сан правила."))

    btns = ft.Row([
        ft.ElevatedButton("М'ясо (Клейма)", on_click=fast_check),
        ft.ElevatedButton("Молоко (ПЕТ-тара)", on_click=fast_check),
        ft.ElevatedButton("Риба (Експертиза)", on_click=fast_check),
        ft.ElevatedButton("Штрафи (КУпАП)", on_click=fast_check),
    ], wrap=True)

    # Поле для вільного питання
    user_input = ft.TextField(label="Спитати про інший Наказ...", multiline=False, expand=True)
    send_btn = ft.IconButton(icon=ft.icons.SEND_ROUNDED, on_click=lambda _: ask_ai(user_input.value))

    # Секція налаштування платного ключа (прихована внизу)
    def change_key(e):
        page.client_storage.set("api_key", key_input.value)
        page.snack_bar = ft.SnackBar(ft.Text("Ключ збережено! Перезапустіть додаток."))
        page.snack_bar.open = True
        page.update()

    key_input = ft.TextField(label="Вставити платний ключ", password=True, can_reveal_password=True)
    key_btn = ft.TextButton("Оновити ключ", on_click=change_key)

    # Збірка екрана
    page.add(
        header,
        btns,
        ft.Row([user_input, send_btn]),
        ft.Container(chat_display, padding=10, border=ft.border.all(1, "grey"), border_radius=10),
        ft.ExpansionTile(
            title=ft.Text("Налаштування (Платний ключ)"),
            controls=[key_input, key_btn]
        )
    )

ft.app(target=main)
