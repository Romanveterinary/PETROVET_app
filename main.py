import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("✅ УРА! АНДРОЇД ПРАЦЮЄ!", size=30, color="green", weight=ft.FontWeight.BOLD))
    page.update()

ft.app(target=main)
