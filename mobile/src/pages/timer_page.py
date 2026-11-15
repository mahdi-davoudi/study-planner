"""Study timer: pick a subject, Start / Pause / Resume / Stop & Save."""

from __future__ import annotations

import flet as ft

from i18n import localize_digits, tr
from palette import C
from timer_state import IDLE, PAUSED, RUNNING, round_minutes
from ui import button, card, confirm, muted, page_column, title
from utils.helpers import minutes_to_hm_text


def _clock_text(seconds: float) -> str:
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    return localize_digits(f"{hours:02d}:{minutes:02d}:{secs:02d}")


def _preview_text(timer, seconds: float) -> str:
    if timer.state == IDLE:
        return ""
    return tr("timer.preview", time=minutes_to_hm_text(round_minutes(seconds)))


def build(app) -> ft.Control:
    db, timer = app.db, app.timer
    subjects = db.get_subjects()
    ids = [s["_id"] for s in subjects]
    if app.timer_subject_id not in ids:
        app.timer_subject_id = ids[0] if ids else None

    # --- live clock (updated by App.tick_loop through app.on_tick) ---
    seconds = timer.elapsed()
    display = ft.Text(
        _clock_text(seconds),
        size=56,
        weight=ft.FontWeight.BOLD,
        color=C.TEXT,
        text_align=ft.TextAlign.CENTER,
    )
    preview = ft.Text(
        _preview_text(timer, seconds),
        color=C.ACCENT,
        weight=ft.FontWeight.W_600,
        text_align=ft.TextAlign.CENTER,
    )

    def tick() -> None:
        current = timer.elapsed()
        display.value = _clock_text(current)
        preview.value = _preview_text(timer, current)
        display.update()
        preview.update()

    app.on_tick = tick

    # --- actions -----------------------------------------------------
    def on_start(e) -> None:
        sid = app.timer_subject_id
        name = next((s["name"] for s in subjects if s["_id"] == sid), "")
        if sid is None:
            return
        app.timer_status = ""
        timer.start(sid, name)
        app.render()

    def on_pause(e) -> None:
        timer.pause()
        app.render()

    def on_resume(e) -> None:
        timer.resume()
        app.render()

    def on_stop(e) -> None:
        total_seconds, day = timer.elapsed(), timer.day
        sid, fallback_name = timer.subject_id, timer.subject_name
        timer.reset()

        minutes = round_minutes(total_seconds)
        if minutes <= 0:
            app.timer_status = tr("timer.too_short")
        else:
            # The subject may have been renamed or deleted while the timer ran.
            names = {s["_id"]: s["name"] for s in db.get_subjects()}
            if sid not in names:
                sid = None
            name = names.get(sid, fallback_name)
            db.add_logs_bulk(
                day,
                [{"subject_id": sid, "subject_name": name, "duration_minutes": minutes}],
            )
            day_total = sum(
                log["duration_minutes"]
                for log in db.get_logs_by_date(day)
                if log["subject_id"] == sid and log["subject_name"] == name
            )
            app.timer_status = tr(
                "timer.saved",
                time=minutes_to_hm_text(minutes),
                name=name,
                total=minutes_to_hm_text(day_total),
            )
        app.render()

    def on_discard(e) -> None:
        def do_discard() -> None:
            timer.reset()
            app.render()

        confirm(app.page, tr("timer.discard_q"), do_discard, heading=tr("common.notice"))

    # --- subject picker ----------------------------------------------
    def pick(sid: int) -> None:
        app.timer_subject_id = sid
        app.render()

    if not subjects:
        subject_area: ft.Control = muted(tr("add.no_subjects"))
    elif timer.state == IDLE:
        subject_area = ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        s["name"],
                        color="#ffffff" if s["_id"] == app.timer_subject_id else C.TEXT,
                    ),
                    bgcolor=C.ACCENT if s["_id"] == app.timer_subject_id else C.BTN,
                    border_radius=18,
                    padding=10,
                    on_click=lambda e, sid=s["_id"]: pick(sid),
                )
                for s in subjects
            ],
            wrap=True,
            spacing=8,
            run_spacing=8,
        )
    else:
        subject_area = ft.Container()

    if timer.state == IDLE:
        state_text = tr("timer.idle") if subjects else tr("add.no_subjects")
    elif timer.state == RUNNING:
        state_text = tr("timer.running", name=timer.subject_name)
    else:
        state_text = tr("timer.paused", name=timer.subject_name)

    # --- buttons -----------------------------------------------------
    if timer.state == IDLE:
        main_btn = button(
            tr("timer.start"), on_start, "primary",
            disabled=app.timer_subject_id is None, expand=True,
        )
    elif timer.state == RUNNING:
        main_btn = button(tr("timer.pause"), on_pause, "warning", expand=True)
    else:
        main_btn = button(tr("timer.resume"), on_resume, "primary", expand=True)

    idle = timer.state == IDLE
    stop_btn = button(tr("timer.stop"), on_stop, "primary", disabled=idle, expand=True)
    discard_btn = button(tr("timer.discard"), on_discard, "danger", disabled=idle)

    timer_card = card(
        subject_area,
        display,
        muted(state_text),
        preview,
        ft.Row([main_btn, stop_btn], spacing=8),
        discard_btn,
        heading=tr("timer.card"),
    )

    controls: list[ft.Control] = [title(tr("timer.title")), timer_card]
    if app.timer_status:
        controls.append(card(ft.Text(app.timer_status, color=C.SUCCESS)))
    return page_column(*controls)
