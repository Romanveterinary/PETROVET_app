import flet as ft
import urllib.request
import json
import base64

def main(page: ft.Page):
    # Дозволяємо екрану прокручуватися
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # 1. ЦЕЙ ТЕКСТ ВИ ТОЧНО МАЄТЕ ПОБАЧИТИ
    page.add(ft.Text("✅ ЕТАП 1: Успішний запуск!", color=ft.colors.GREEN_700, size=22, weight=ft.FontWeight.BOLD))

    # 2. ТЕСТУЄМО ІНТЕРФЕЙС (чи не падає він від полів вводу)
    try:
        page.add(ft.TextField(label="Тестове поле вводу (натисніть)"))
        page.add(ft.Dropdown(label="Тестовий список", options=[ft.dropdown.Option("Варіант 1")]))
        page.add(ft.Text("✅ ЕТАП 2: Інтерфейс намальовано!", color=ft.colors.GREEN_700))
    except Exception as e:
        page.add(ft.Text(f"❌ Помилка інтерфейсу: {e}", color=ft.colors.RED))

    # 3. ТЕСТУЄМО ГАЛЕРЕЮ (FilePicker)
    try:
        def on_pick(e: ft.FilePickerResultEvent):
            if e.files:
                page.add(ft.Text(f"📁 Обрано файлів: {len(e.files)}", color=ft.colors.BLUE_900))
            else:
                page.add(ft.Text("Скасовано вибір фото.", color=ft.colors.GREY))
            page.update()

        file_picker = ft.FilePicker(on_result=on_pick)
        page.overlay.append(file_picker)
        
        page.add(ft.ElevatedButton("Відкрити галерею", icon=ft.icons.IMAGE, on_click=lambda _: file_picker.pick_files()))
        page.add(ft.Text("✅ ЕТАП 3: Галерея підключена!", color=ft.colors.GREEN_700))
    except Exception as e:
        page.add(ft.Text(f"❌ Помилка галереї: {e}", color=ft.colors.RED))

    page.update()

ft.app(target=main)
