"""Reports: distribution of study time per subject for a chosen period."""

from __future__ import annotations

from datetime import date, timedelta

import flet as ft

from i18n import isolate, localize_digits, tr
from palette import C
from ui import card, muted, page_column, stat_card, title
from utils.helpers import minutes_to_hm_text

PRESETS = [
    ("today", "common.today"),
    ("7", "preset.7"),
    ("30", "preset.30"),
    ("month", "stat.month"),
    ("year", "preset.year"),
    ("all", "preset.all"),
]


def _range(key: str, today: date) -> tuple[date | None, date | None]:
    if key == "today":
        return today, today
    if key == "7":
        return today - timedelta(days=6), today
    if key == "30":
        return today - timedelta(days=29), today
    if key == "month":
        return today.replace(day=1), today
    if key == "year":
        return today.replace(month=1, day=1), today
    return None, None


def build(app) -> ft.Control:
    db = app.db
    today = date.today()
    start, end = _range(app.report_range, today)

    if start is None or end is None:
        summary = db.get_subject_percentages()
        caption = tr("rep.showing_all")
    else:
        summary = db.get_subject_percentages(start.isoformat(), end.isoformat())
        caption = tr("rep.showing", start=start.isoformat(), end=end.isoformat())

    def choose(key: str) -> None:
        app.report_range = key
        app.render()

    chips = ft.Row(
        [
            ft.Container(
                content=ft.Text(
                    tr(label),
                    size=13,
                    color="#ffffff" if key == app.report_range else C.TEXT,
                ),
                bgcolor=C.ACCENT if key == app.report_range else C.BTN,
                border_radius=16,
                padding=8,
                on_click=lambda e, key=key: choose(key),
            )
            for key, label in PRESETS
        ],
        wrap=True,
        spacing=6,
        run_spacing=6,
    )
    controls: list[ft.Control] = [
        title(tr("rep.title")),
        card(chips, muted(caption), heading=tr("rep.range_card")),
    ]

    if not summary:
        controls.append(card(muted(tr("rep.no_data"))))
        return page_column(*controls)

    colors = [C.SLICE_COLORS[i % len(C.SLICE_COLORS)] for i in range(len(summary))]

    # Stacked bar: every segment is as wide as that subject's share.
    bar = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    expand=max(1, int(item["total_minutes"])),
                    bgcolor=color,
                    height=18,
                )
                for item, color in zip(summary, colors)
            ],
            spacing=0,
        ),
        border_radius=9,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )
    legend = [
        ft.Row(
            [
                ft.Container(width=12, height=12, bgcolor=color, border_radius=3),
                ft.Text(item["subject_name"], expand=True, color=C.TEXT),
                ft.Text(minutes_to_hm_text(item["total_minutes"]), size=12, color=C.MUTED),
                ft.Text(
                    localize_digits(f"{item['percentage']:.1f}%"),
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=C.TEXT,
                ),
            ],
            spacing=8,
        )
        for item, color in zip(summary, colors)
    ]
    controls.append(card(bar, *legend, heading=tr("rep.distribution")))

    total = sum(item["total_minutes"] for item in summary)
    most, least = summary[0], summary[-1]

    def name_with_time(item: dict) -> str:
        return f"{isolate(item['subject_name'])} ({minutes_to_hm_text(item['total_minutes'])})"

    controls.append(
        ft.Row(
            [
                stat_card(tr("common.total"), minutes_to_hm_text(total), C.SUCCESS),
                stat_card(
                    tr("rep.average"),
                    minutes_to_hm_text(round(total / len(summary))),
                    C.ACCENT,
                ),
            ],
            spacing=8,
        )
    )
    controls.append(
        ft.Row(
            [
                stat_card(tr("rep.most"), name_with_time(most), C.ORANGE),
                stat_card(tr("rep.least"), name_with_time(least), C.MUTED),
            ],
            spacing=8,
        )
    )
    return page_column(*controls)
