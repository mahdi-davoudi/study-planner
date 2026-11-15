"""Subjects: add, rename, delete."""

from __future__ import annotations

import flet as ft

from i18n import tr
from palette import C
from ui import button, card, confirm, muted, page_column, prompt, snack, title


def build(app) -> ft.Control:
    db = app.db
    name_field = ft.TextField(hint_text=tr("sub.placeholder"), dense=True, expand=True)

    def add(e) -> None:
        name = (name_field.value or "").strip()
        if not name:
            snack(app.page, tr("sub.enter_name"))
            return
        if name in {s["name"] for s in db.get_subjects()}:
            snack(app.page, tr("sub.exists"))
            return
        db.add_subject(name)
        app.render()

    def rename(subject: dict) -> None:
        def apply(value: str) -> None:
            new_name = value.strip()
            if not new_name or new_name == subject["name"]:
                return
            if not db.rename_subject(subject["_id"], new_name):
                snack(app.page, tr("sub.exists_other"))
                return
            app.render()

        prompt(app.page, tr("sub.rename_title"), tr("sub.new_name"), subject["name"], apply)

    def delete(subject: dict) -> None:
        def do_delete() -> None:
            db.delete_subject(subject["_id"])
            app.render()

        confirm(app.page, tr("sub.delete_q", name=subject["name"]), do_delete)

    add_card = card(
        ft.Row([name_field, button(tr("sub.add_btn"), add, "primary")], spacing=8),
        heading=tr("sub.add_card"),
    )

    subjects = db.get_subjects()
    if subjects:
        rows: list[ft.Control] = [
            ft.Row(
                [
                    ft.Text(s["name"], expand=True, color=C.TEXT),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=C.MUTED,
                        on_click=lambda e, s=s: rename(s),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=C.DANGER,
                        on_click=lambda e, s=s: delete(s),
                    ),
                ],
                spacing=0,
            )
            for s in subjects
        ]
    else:
        rows = [muted(tr("add.no_subjects"))]
    list_card = card(*rows, heading=tr("sub.list_card"))

    return page_column(title(tr("sub.title")), add_card, list_card)
