"""Home page: stats, activity heatmap, log study time, edit/delete a day's records."""

from __future__ import annotations

from datetime import date, timedelta

import flet as ft

from i18n import format_date, tr, tr_n
from palette import C
from ui import (
    border_all,
    button,
    card,
    confirm,
    muted,
    page_column,
    prompt_duration,
    snack,
    stat_card,
    title,
    total_minutes_from,
    duration_fields,
)
from utils.helpers import minutes_to_hm_text

# A phone screen fits about 18 weeks of the heatmap without scrolling.
WEEKS = 18
CELL = 13
GAP = 2


def _level_color(minutes: int) -> str:
    if minutes <= 0:
        idx = 0
    elif minutes <= 30:
        idx = 1
    elif minutes <= 90:
        idx = 2
    elif minutes <= 180:
        idx = 3
    else:
        idx = 4
    return C.HEAT_COLORS[idx]


def _grid_start(today: date) -> date:
    monday = today - timedelta(days=today.weekday())
    return monday - timedelta(weeks=WEEKS - 1)


def _heatmap(app, totals: dict[str, int], today: date) -> ft.Control:
    start = _grid_start(today)
    columns = []
    for week in range(WEEKS):
        cells = []
        for dow in range(7):
            day = start + timedelta(days=week * 7 + dow)
            if day > today:
                cells.append(ft.Container(width=CELL, height=CELL))
                continue
            border = None
            if day == app.selected_date:
                border = border_all(2, C.TEXT)
            elif day == today:
                border = border_all(2, C.ORANGE)
            cells.append(
                ft.Container(
                    width=CELL,
                    height=CELL,
                    border_radius=3,
                    bgcolor=_level_color(totals.get(day.isoformat(), 0)),
                    border=border,
                    on_click=lambda e, d=day: app.select_day(d),
                )
            )
        columns.append(ft.Column(cells, spacing=GAP))

    legend = ft.Row(
        [muted(tr("heat.less"), 11)]
        + [
            ft.Container(width=CELL - 2, height=CELL - 2, border_radius=3, bgcolor=color)
            for color in C.HEAT_COLORS
        ]
        + [muted(tr("heat.more"), 11)],
        spacing=4,
        alignment=ft.MainAxisAlignment.END,
    )
    return ft.Column(
        [ft.Row(columns, spacing=GAP, alignment=ft.MainAxisAlignment.CENTER), legend],
        spacing=8,
    )


def build(app) -> ft.Control:
    db = app.db
    today = date.today()
    if app.selected_date > today:
        app.selected_date = today
    iso = app.selected_date.isoformat()

    # --- stats -------------------------------------------------------
    streak = db.get_current_streak()
    stats = ft.Row(
        [
            stat_card(tr("stat.streak"), tr_n("streak", streak), C.ORANGE),
            stat_card(tr("stat.week"), minutes_to_hm_text(db.get_week_total()), C.ACCENT),
            stat_card(tr("stat.month"), minutes_to_hm_text(db.get_month_total()), C.SUCCESS),
        ],
        spacing=8,
    )

    # --- heatmap -----------------------------------------------------
    totals = db.get_daily_totals(_grid_start(today).isoformat(), today.isoformat())
    heat_card = card(_heatmap(app, totals, today), heading=tr("add.activity"))

    # --- date picker row --------------------------------------------
    date_row = ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_color=C.TEXT,
                on_click=lambda e: app.select_day(app.selected_date - timedelta(days=1)),
            ),
            ft.Text(
                format_date(app.selected_date),
                expand=True,
                text_align=ft.TextAlign.CENTER,
                color=C.TEXT,
                weight=ft.FontWeight.W_600,
            ),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                icon_color=C.TEXT,
                disabled=app.selected_date >= today,
                on_click=lambda e: app.select_day(app.selected_date + timedelta(days=1)),
            ),
        ]
    )
    today_btn = button(
        tr("common.today"),
        lambda e: app.select_day(today),
        disabled=app.selected_date == today,
    )

    # --- log form ----------------------------------------------------
    subjects = db.get_subjects()
    fields: dict[int, tuple[ft.TextField, ft.TextField]] = {}
    form_rows: list[ft.Control] = []
    for subject in subjects:
        hours_field, minutes_field = duration_fields(
            0, tr("add.hours_label"), tr("add.minutes_label"), expand=True
        )
        fields[subject["_id"]] = (hours_field, minutes_field)
        form_rows.append(
            ft.Column(
                [
                    ft.Text(subject["name"], color=C.TEXT, weight=ft.FontWeight.W_500),
                    ft.Row([hours_field, minutes_field], spacing=8),
                ],
                spacing=4,
            )
        )

    def save(e) -> None:
        entries = []
        for subject in subjects:
            hours_field, minutes_field = fields[subject["_id"]]
            minutes = total_minutes_from(hours_field, minutes_field)
            if minutes > 0:
                entries.append(
                    {
                        "subject_id": subject["_id"],
                        "subject_name": subject["name"],
                        "duration_minutes": minutes,
                    }
                )
        if not entries:
            snack(app.page, tr("add.need_minutes"))
            return
        count = db.add_logs_bulk(iso, entries)
        total = sum(item["duration_minutes"] for item in entries)
        snack(app.page, tr_n("add.saved", count, iso=iso, total=minutes_to_hm_text(total)))
        app.render()

    if subjects:
        form_body: list[ft.Control] = [date_row, today_btn, *form_rows]
        form_body.append(button(tr("add.save"), save, "primary"))
    else:
        form_body = [muted(tr("add.no_subjects"))]
    form_card = card(*form_body, heading=tr("add.log_card"))

    # --- records of the selected day (edit / delete) ----------------
    def edit_log(log: dict) -> None:
        def apply(minutes: int) -> None:
            if minutes > 0 and minutes != log["duration_minutes"]:
                db.update_log_duration(log["_id"], minutes)
            app.render()

        prompt_duration(
            app.page,
            tr("edit.dialog_title"),
            log["subject_name"],
            log["duration_minutes"],
            apply,
        )

    def delete_log(log: dict) -> None:
        def do_delete() -> None:
            db.delete_log(log["_id"])
            app.render()

        confirm(
            app.page,
            tr(
                "edit.delete_q",
                name=log["subject_name"],
                time=minutes_to_hm_text(log["duration_minutes"]),
            ),
            do_delete,
        )

    logs = db.get_logs_by_date(iso)
    if logs:
        record_rows: list[ft.Control] = [
            ft.Row(
                [
                    ft.Text(log["subject_name"], expand=True, color=C.TEXT),
                    ft.Text(
                        minutes_to_hm_text(log["duration_minutes"]),
                        color=C.MUTED,
                        size=13,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=C.MUTED,
                        on_click=lambda e, log=log: edit_log(log),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=C.DANGER,
                        on_click=lambda e, log=log: delete_log(log),
                    ),
                ],
                spacing=0,
            )
            for log in logs
        ]
        total_minutes = sum(log["duration_minutes"] for log in logs)
        record_rows.append(
            ft.Text(
                f"{tr('common.total')}: {minutes_to_hm_text(total_minutes)}",
                weight=ft.FontWeight.BOLD,
                color=C.TEXT,
            )
        )
    else:
        record_rows = [muted(tr("add.no_records"))]
    records_card = card(*record_rows, heading=tr("add.day_title", iso=iso))

    return page_column(title(tr("add.title")), stats, heat_card, form_card, records_card)
