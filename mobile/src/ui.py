"""Small reusable UI helpers shared by all pages."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from config import SPIN_MAX_MINUTES
from i18n import tr
from palette import C

MAX_HOURS = SPIN_MAX_MINUTES // 60  # 12
MAX_MINUTES = 59  # 60 minutes is entered as 1 hour


def border_all(width: float, color: str):
    return ft.Border.all(width, color)


def title(text: str) -> ft.Text:
    return ft.Text(text, size=24, weight=ft.FontWeight.BOLD, color=C.TEXT)


def muted(text: str, size: int = 13) -> ft.Text:
    return ft.Text(text, size=size, color=C.MUTED)


def page_column(*controls: ft.Control) -> ft.Column:
    return ft.Column(
        list(controls),
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        expand=True,
    )


def card(*controls: ft.Control, heading: str | None = None) -> ft.Container:
    items: list[ft.Control] = []
    if heading:
        items.append(
            ft.Text(heading, size=16, weight=ft.FontWeight.W_600, color=C.TEXT)
        )
    items.extend(controls)
    return ft.Container(
        content=ft.Column(
            items, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        ),
        bgcolor=ft.Colors.with_opacity(C.CARD_ALPHA, C.CARD),
        border_radius=12,
        padding=14,
    )


def stat_card(caption: str, value: str, color: str) -> ft.Container:
    return ft.Container(
        expand=True,
        bgcolor=C.CARD,
        border_radius=12,
        padding=10,
        content=ft.Column(
            [
                ft.Text(caption, size=11, color=C.MUTED),
                ft.Text(value, size=14, weight=ft.FontWeight.BOLD, color=color),
            ],
            spacing=2,
        ),
    )


def button(
    text: str,
    on_click: Callable,
    kind: str = "normal",
    disabled: bool = False,
    expand: bool = False,
) -> ft.Button:
    background = {
        "primary": C.PRIMARY,
        "warning": C.WARN_BG,
        "danger": C.DANGER_BG,
    }.get(kind, C.BTN)
    foreground = C.TEXT if kind == "normal" else "#ffffff"
    return ft.Button(
        text,
        on_click=on_click,
        bgcolor=background,
        color=foreground,
        disabled=disabled,
        expand=expand,
    )


def snack(page: ft.Page, message: str) -> None:
    page.show_dialog(ft.SnackBar(content=ft.Text(message)))


def confirm(
    page: ft.Page, message: str, on_yes: Callable[[], None], heading: str | None = None
) -> None:
    def _yes(e) -> None:
        page.pop_dialog()
        on_yes()

    def _no(e) -> None:
        page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text(heading or tr("common.confirm_delete")),
            content=ft.Text(message),
            actions=[
                ft.TextButton(tr("common.no"), on_click=_no),
                ft.TextButton(tr("common.yes"), on_click=_yes),
            ],
        )
    )


def prompt(
    page: ft.Page,
    heading: str,
    label: str,
    initial: object,
    on_ok: Callable[[str], None],
    numeric: bool = False,
) -> None:
    field = ft.TextField(
        label=label,
        value=str(initial),
        autofocus=True,
        keyboard_type=ft.KeyboardType.NUMBER if numeric else ft.KeyboardType.TEXT,
    )

    def _ok(e) -> None:
        page.pop_dialog()
        on_ok(field.value or "")

    def _cancel(e) -> None:
        page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text(heading),
            content=field,
            actions=[
                ft.TextButton(tr("common.cancel"), on_click=_cancel),
                ft.TextButton(tr("common.save"), on_click=_ok),
            ],
        )
    )


# ---------------------------------------------------------------------------
# Hours + minutes input
# ---------------------------------------------------------------------------
def parse_int(text: str | None) -> int:
    """Digits only (Persian digits are fine); anything else counts as 0."""
    digits = "".join(ch for ch in (text or "") if ch.isdecimal())
    return int(digits) if digits else 0


def _limit_digits(field: ft.TextField, maximum: int) -> Callable:
    def handler(e) -> None:
        raw = field.value or ""
        cleaned = "".join(ch for ch in raw if ch.isdecimal())
        if cleaned and int(cleaned) > maximum:
            cleaned = str(maximum)
        if cleaned != raw:
            field.value = cleaned
            field.update()

    return handler


limit_digits = _limit_digits


def duration_fields(
    total_minutes: int = 0,
    hours_label: str | None = None,
    minutes_label: str | None = None,
    expand: bool = False,
    width: int | None = None,
) -> tuple[ft.TextField, ft.TextField]:
    """Two number boxes (hours, minutes). Minutes can't go above 59 and the
    hours can't go above 12; bigger values are corrected while typing."""
    hours, minutes = divmod(max(0, int(total_minutes)), 60)

    def make(value: int, maximum: int, label: str | None) -> ft.TextField:
        field = ft.TextField(
            value=str(value) if value else "",
            hint_text="0",
            label=label,
            dense=True,
            expand=expand,
            width=width,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        field.on_change = _limit_digits(field, maximum)
        return field

    return make(hours, MAX_HOURS, hours_label), make(minutes, MAX_MINUTES, minutes_label)


def total_minutes_from(hours_field: ft.TextField, minutes_field: ft.TextField) -> int:
    total = parse_int(hours_field.value) * 60 + parse_int(minutes_field.value)
    return min(total, SPIN_MAX_MINUTES)


def prompt_duration(
    page: ft.Page,
    heading: str,
    subject_name: str,
    total_minutes: int,
    on_ok: Callable[[int], None],
) -> None:
    hours_field, minutes_field = duration_fields(
        total_minutes, tr("add.hours_label"), tr("add.minutes_label"), expand=True
    )

    def _ok(e) -> None:
        page.pop_dialog()
        on_ok(total_minutes_from(hours_field, minutes_field))

    def _cancel(e) -> None:
        page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text(heading),
            content=ft.Column(
                [ft.Text(subject_name), ft.Row([hours_field, minutes_field], spacing=8)],
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton(tr("common.cancel"), on_click=_cancel),
                ft.TextButton(tr("common.save"), on_click=_ok),
            ],
        )
    )

