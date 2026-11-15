from __future__ import annotations

import asyncio
from datetime import date

import flet as ft

import i18n
from database import DatabaseManager
from i18n import tr
from pages import add_page, report_page, settings_page, subjects_page, timer_page
from palette import C, set_theme
from reminders import Reminders
from timer_state import StudyTimer
from utils.helpers import parse_hhmm

NAV = [
    ("nav.add", ft.Icons.ADD_CIRCLE_OUTLINE),
    ("nav.timer", ft.Icons.TIMER),
    ("nav.reports", ft.Icons.PIE_CHART),
    ("nav.subjects", ft.Icons.BOOK),
    ("nav.settings", ft.Icons.SETTINGS),
]


class App:
    """Holds the shared state; pages are plain functions build(app) -> control."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.db = DatabaseManager()
        self.timer = StudyTimer(self.db)
        self.reminders = Reminders()

        # UI state shared between pages
        self.index = 0
        self.selected_date = date.today()
        self.timer_subject_id: int | None = None
        self.timer_status = ""
        self.report_range = "month"
        self.on_tick = None  # set by the timer page, called twice a second

        i18n.manager.set_language(self.db.get_setting("language", i18n.DEFAULT_LANGUAGE))
        self.theme = set_theme(self.db.get_setting("theme", "dark"))

        self.pages = [
            add_page.build,
            timer_page.build,
            report_page.build,
            subjects_page.build,
            settings_page.build,
        ]
        self.body = ft.Container(expand=True, padding=14)
        page.padding = 0
        page.add(ft.SafeArea(expand=True, content=self.body))
        self.rebuild()

    # ------------------------------------------------------------------
    def rebuild(self) -> None:
        page = self.page
        page.title = tr("app.name")
        page.rtl = i18n.manager.is_rtl
        page.theme_mode = ft.ThemeMode.DARK if self.theme == "dark" else ft.ThemeMode.LIGHT
        page.bgcolor = C.BG
        
        dark = self.theme == "dark"
        self.body.image = ft.DecorationImage(
            src="bg_dark.jpg" if dark else "bg_light.jpg",
            fit=ft.BoxFit.COVER,
            opacity=0.5 if dark else 0.35,
        )
        
        page.navigation_bar = ft.NavigationBar(
            selected_index=self.index,
            bgcolor=C.CARD,
            on_change=self._on_nav,
            destinations=[
                ft.NavigationBarDestination(icon=icon, label=tr(key)) for key, icon in NAV
            ],
        )
        self.render()

    def render(self) -> None:
        self.on_tick = None  # the timer page registers it again when built
        self.body.content = self.pages[self.index](self)
        self.page.update()

    def _on_nav(self, e) -> None:
        self.index = e.control.selected_index
        self.render()

    # ------------------------------------------------------------------
    def select_day(self, day: date) -> None:
        self.selected_date = min(day, date.today())
        self.render()

    def set_language(self, code: str) -> None:
        i18n.manager.set_language(code)
        self.db.set_setting("language", code)
        self.rebuild()
        self.page.run_task(self.sync_reminder)  # notification text is translated

    def set_theme(self, name: str) -> None:
        self.theme = set_theme(name)
        self.db.set_setting("theme", self.theme)
        self.rebuild()

    # ------------------------------------------------------------------
    async def sync_reminder(self, interactive: bool = False) -> str:
        enabled = self.db.get_setting("reminder.enabled", "0") == "1"
        hour, minute = parse_hhmm(self.db.get_setting("reminder.time", "20:00")) or (20, 0)
        return await self.reminders.apply(
            enabled, hour, minute, tr("reminder.title"), tr("reminder.body"), interactive
        )

    async def tick_loop(self) -> None:
        while True:
            await asyncio.sleep(0.5)
            callback = self.on_tick
            if callback is not None:
                try:
                    callback()
                except Exception:
                    pass  # page was replaced while we were updating it


def main(page: ft.Page) -> None:
    app = App(page)
    page.run_task(app.tick_loop)
    page.run_task(app.sync_reminder)


ft.run(main)
