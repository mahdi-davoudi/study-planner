"""Settings: language, theme and the daily reminder."""

from __future__ import annotations

import flet as ft

import i18n
from i18n import localize_digits, tr
from palette import C
from ui import button, card, limit_digits, muted, page_column, parse_int, snack, title
from utils.helpers import parse_hhmm, to_12h, to_24h


def build(app) -> ft.Control:
    db = app.db

    language_row = ft.Row(
        [
            button(
                name,
                lambda e, code=code: app.set_language(code),
                "primary" if code == i18n.manager.language else "normal",
                expand=True,
            )
            for code, name in i18n.LANGUAGES.items()
        ],
        spacing=8,
    )
    theme_row = ft.Row(
        [
            button(
                tr(label),
                lambda e, name=name: app.set_theme(name),
                "primary" if name == app.theme else "normal",
                expand=True,
            )
            for name, label in (("dark", "settings.dark"), ("light", "settings.light"))
        ],
        spacing=8,
    )

    # --- reminder (12-hour clock with AM / PM) -----------------------
    enabled_switch = ft.Switch(
        value=db.get_setting("reminder.enabled", "0") == "1",
        label=tr("settings.reminder_on"),
    )
    saved_hour, saved_minute = parse_hhmm(db.get_setting("reminder.time", "20:00")) or (20, 0)
    hour12, suffix = to_12h(saved_hour)
    chosen = {"suffix": suffix}

    hour_field = ft.TextField(
        label=tr("settings.hour"),
        value=str(hour12),
        hint_text="8",
        dense=True,
        expand=True,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    hour_field.on_change = limit_digits(hour_field, 12)
    minute_field = ft.TextField(
        label=tr("settings.minute"),
        value=f"{saved_minute:02d}",
        hint_text="00",
        dense=True,
        expand=True,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    minute_field.on_change = limit_digits(minute_field, 59)

    def paint_ampm() -> None:
        for value, btn in (("am", am_btn), ("pm", pm_btn)):
            active = chosen["suffix"] == value
            btn.bgcolor = C.PRIMARY if active else C.BTN
            btn.color = "#ffffff" if active else C.TEXT

    def pick(value: str):
        def handler(e) -> None:
            chosen["suffix"] = value
            paint_ampm()
            am_btn.update()
            pm_btn.update()

        return handler

    am_btn = button(tr("settings.am"), pick("am"), expand=True)
    pm_btn = button(tr("settings.pm"), pick("pm"), expand=True)
    paint_ampm()

    def shown_time(hour24: int, minute: int) -> str:
        h12, suffix_ = to_12h(hour24)
        label = tr("settings.am") if suffix_ == "am" else tr("settings.pm")
        return localize_digits(f"{h12}:{minute:02d}") + " " + label

    async def save_reminder(e) -> None:
        hour_value = parse_int(hour_field.value)
        minute_value = parse_int(minute_field.value)
        if not 1 <= hour_value <= 12 or minute_value > 59:
            snack(app.page, tr("settings.bad_time"))
            return
        hour24 = to_24h(hour_value, chosen["suffix"])
        db.set_setting("reminder.enabled", "1" if enabled_switch.value else "0")
        db.set_setting("reminder.time", f"{hour24:02d}:{minute_value:02d}")

        status = await app.sync_reminder(interactive=True)
        shown = shown_time(hour24, minute_value)
        messages = {
            "scheduled": tr("settings.reminder_scheduled", time=shown),
            "scheduled_inexact": tr("settings.reminder_inexact", time=shown),
            "cancelled": tr("settings.reminder_cancelled"),
            "denied": tr("settings.reminder_denied"),
            "unavailable": tr("settings.reminder_unavailable"),
            "error": tr("settings.reminder_error"),
        }
        snack(app.page, messages.get(status, status))

    async def send_test(e) -> None:
        status = await app.reminders.test(tr("reminder.title"), tr("reminder.body"))
        messages = {
            "sent": tr("settings.test_sent"),
            "denied": tr("settings.reminder_denied"),
            "unavailable": tr("settings.reminder_unavailable"),
            "error": tr("settings.reminder_error"),
        }
        snack(app.page, messages.get(status, status))

    return page_column(
        title(tr("settings.title")),
        card(language_row, heading=tr("settings.language")),
        card(theme_row, heading=tr("settings.theme")),
        card(
            enabled_switch,
            muted(tr("settings.reminder_time"), 12),
            ft.Row([hour_field, minute_field], spacing=8),
            ft.Row([am_btn, pm_btn], spacing=8),
            button(tr("settings.reminder_save"), save_reminder, "primary"),
            button(tr("settings.reminder_test"), send_test),
            muted(tr("reminder.body"), 12),
            heading=tr("settings.reminder"),
        ),
    )
