import flet as ft
import time
import traceback

def main(page: ft.Page):
    page.title = "ДІАГНОСТИКА"
    page.padding = 20
    
    # Створюємо список для виводу логів на екран
    log = ft.ListView(expand=True, spacing=10)
    page.add(log)

    def add_log(text, color="black", weight=ft.FontWeight.NORMAL):
        log.controls.append(ft.Text(text, color=color, weight=weight))
        page.update()
        time.sleep(0.8) # Пауза, щоб ви встигли прочитати

    try:
        add_log("✅ 1. Flet успішно запущено!", ft.colors.GREEN, ft.FontWeight.BOLD)
        
        add_log("⏳ 2. Тестую імпорт бібліотек (urllib, json, base64)...")
        import urllib.request
        import json
        import base64
        import os
        import datetime
        add_log("✅ Бібліотеки завантажено!", ft.colors.GREEN)

        add_log("⏳ 3. Тестую пам'ять телефону (client_storage)...")
        page.client_storage.set("test_key", "123")
        test_val = page.client_storage.get("test_key")
        add_log(f"✅ Пам'ять працює! (Тест: {test_val})", ft.colors.GREEN)

        add_log("⏳ 4. Тестую інструмент вибору фото (FilePicker)...")
        file_picker = ft.FilePicker()
        page.overlay.append(file_picker)
        page.update()
        add_log("✅ FilePicker успішно підключено!", ft.colors.GREEN)

        add_log("⏳ 5. Тестую складні елементи інтерфейсу...")
        page.add(ft.TextField(label="Тестове поле"))
        page.add(ft.Dropdown(options=[ft.dropdown.Option("Тест")]))
        add_log("✅ Інтерфейс намальовано!", ft.colors.GREEN)

        add_log("🎉 ВСІ ТЕСТИ ПРОЙДЕНО УСПІШНО! Проблема ховалася десь інде.", ft.colors.BLUE, ft.FontWeight.BOLD)

    except Exception as e:
        add_log("🚨 ЗНАЙДЕНО ПОМИЛКУ!", ft.colors.RED, ft.FontWeight.BOLD)
        add_log(str(e), ft.colors.RED)
        add_log(traceback.format_exc(), ft.colors.RED)

ft.app(target=main)
