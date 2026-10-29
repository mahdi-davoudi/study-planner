import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import tkinter as tk
from datetime import datetime, timedelta
from collections.abc import Callable
from utils.helpers import today_str, is_valid_date, minutes_to_hm_text

SPIN_MAX_MINUTES = 240  
SPIN_STEP = 5  

# Heatmap visual constants
CELL_SIZE = 12
CELL_GAP = 3
CELL_RADIUS = 2
CANVAS_HEIGHT = (CELL_SIZE + CELL_GAP) * 7 + 20
MIN_LABEL_GAP = 28 

COLOR_EMPTY = "#1c2128"        
COLOR_LIGHT = "#2d5a3d"        
COLOR_MEDIUM = "#3f9e58"       
COLOR_DARK = "#1c6b32"         
COLOR_BRIGHT = "#39ff6a"       
COLOR_TODAY_BORDER = "#f0ad4e"

WEEKDAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", ""]


def _minutes_to_color(total_minutes: int) -> str:
    if not total_minutes or total_minutes <= 0:
        return COLOR_EMPTY
    if total_minutes <= 30:
        return COLOR_LIGHT
    if total_minutes <= 90:
        return COLOR_MEDIUM
    if total_minutes <= 180:
        return COLOR_DARK
    return COLOR_BRIGHT


class StudyHeatmap(tb.Frame):
    """GitHub-style yearly heatmap of daily study minutes."""

    def __init__(
        self,
        parent: tk.Misc,
        db,
        on_day_click: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.on_day_click = on_day_click

        self._tooltip: tk.Toplevel | None = None
        self._tooltip_label: tk.Label | None = None
        self._hover_item: int | None = None
        self._day_rects: dict[int, tuple[str, int]] = {}  # canvas id -> (date, minutes)

        self.canvas = tk.Canvas(
            self,
            bg="#0d1117",
            highlightthickness=0,
            width=300,  # فقط حداقل؛ عرض واقعی را fill="x" تعیین می‌کند
            height=CANVAS_HEIGHT,
            xscrollincrement=CELL_SIZE + CELL_GAP,  # هر «واحد» اسکرول = یک هفته
        )
        self.h_scroll = tb.Scrollbar(
            self, orient="horizontal", command=self.canvas.xview, bootstyle="round"
        )
        self.canvas.configure(xscrollcommand=self.h_scroll.set)

        self.canvas.pack(side="top", fill="x")
        self.h_scroll.pack(side="top", fill="x")

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._hide_tooltip)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_wheel)

        self.refresh()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Redraw the heatmap for the current year (Jan 1 -> today)."""
        self.canvas.delete("all")
        self._day_rects.clear()
        self._hide_tooltip()

        today = datetime.now().date()
        jan_first = today.replace(month=1, day=1)
        # Grid starts on the Monday of the week that contains Jan 1.
        grid_start = jan_first - timedelta(days=jan_first.weekday())

        daily_totals = self.db.get_daily_totals(
            jan_first.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d"),
        )

        total_weeks = ((today - grid_start).days // 7) + 1
        canvas_width = 30 + total_weeks * (CELL_SIZE + CELL_GAP)
        self.canvas.configure(scrollregion=(0, 0, canvas_width, CANVAS_HEIGHT))

        # Weekday labels
        for row, label in enumerate(WEEKDAY_LABELS):
            if label:
                self.canvas.create_text(
                    12,
                    20 + row * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2,
                    text=label,
                    fill="#8b949e",
                    font=("Segoe UI", 7),
                    anchor="w",
                )

        last_month: int | None = None
        last_label_x = -MIN_LABEL_GAP
        day = grid_start
        col = 0
        while day <= today:
            row = day.weekday()
            x0 = 30 + col * (CELL_SIZE + CELL_GAP)

            # Month label at the first Monday of each month. For the first
            # column we use Jan 1 instead of the padding Monday from December,
            # and we never draw two labels closer than MIN_LABEL_GAP pixels.
            if row == 0:
                label_day = max(day, jan_first)
                if (
                    label_day.month != last_month
                    and x0 - last_label_x >= MIN_LABEL_GAP
                ):
                    last_month = label_day.month
                    last_label_x = x0
                    self.canvas.create_text(
                        x0, 8,
                        text=label_day.strftime("%b"),
                        fill="#8b949e",
                        font=("Segoe UI", 7),
                        anchor="w",
                    )

            # Skip the December days that only pad the first week.
            if day >= jan_first:
                date_str = day.strftime("%Y-%m-%d")
                total_minutes = daily_totals.get(date_str, 0)

                y0 = 20 + row * (CELL_SIZE + CELL_GAP)
                is_today = day == today
                rect_id = self.canvas.create_rectangle(
                    x0, y0, x0 + CELL_SIZE, y0 + CELL_SIZE,
                    fill=_minutes_to_color(total_minutes),
                    outline=COLOR_TODAY_BORDER if is_today else "#0d1117",
                    width=2 if is_today else 1,
                )
                self._day_rects[rect_id] = (date_str, total_minutes)

            if row == 6:
                col += 1
            day += timedelta(days=1)

        # Show the most recent weeks (today) once the layout is settled.
        self.after_idle(self._scroll_to_end)

    # ------------------------------------------------------------------
    # Scrolling
    # ------------------------------------------------------------------
    def _scroll_to_end(self) -> None:
        try:
            self.canvas.xview_moveto(1.0)
        except tk.TclError:  # widget destroyed before the idle callback ran
            pass

    def _on_canvas_configure(self, event: tk.Event) -> None:
        # Window resized: keep today's end of the heatmap visible.
        self._scroll_to_end()

    def _on_shift_wheel(self, event: tk.Event) -> None:
        self.canvas.xview_scroll(-3 if event.delta > 0 else 3, "units")

    # ------------------------------------------------------------------
    # Hit testing
    # ------------------------------------------------------------------
    def _item_at(self, x: int, y: int) -> int | None:
        """Return the day-cell under the point, or None if it is in a gap."""
        # x/y are window coordinates; convert to canvas coordinates so that
        # hit-testing stays correct after horizontal scrolling.
        cx = int(self.canvas.canvasx(x))
        cy = int(self.canvas.canvasy(y))
        for item in self.canvas.find_overlapping(cx, cy, cx, cy):
            if item in self._day_rects:
                return item
        return None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _on_motion(self, event: tk.Event) -> None:
        item = self._item_at(event.x, event.y)
        if item is None:
            self.canvas.configure(cursor="")
            self._hide_tooltip()
            return

        self.canvas.configure(cursor="hand2")
        date_str, total_minutes = self._day_rects[item]
        self._show_tooltip(event, date_str, total_minutes, item)

    def _on_click(self, event: tk.Event) -> None:
        item = self._item_at(event.x, event.y)
        if item is None:
            return
        date_str, _ = self._day_rects[item]
        if self.on_day_click:
            self.on_day_click(date_str)

    # ------------------------------------------------------------------
    # Tooltip
    # ------------------------------------------------------------------
    def _show_tooltip(
        self, event: tk.Event, date_str: str, total_minutes: int, item: int
    ) -> None:
        if self._tooltip is None:
            self._tooltip = tk.Toplevel(self)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.attributes("-topmost", True)
            self._tooltip_label = tk.Label(
                self._tooltip,
                justify="left",
                bg="#161b22",
                fg="#e6edf3",
                font=("Segoe UI", 9),
                padx=8,
                pady=6,
                relief="solid",
                borderwidth=1,
            )
            self._tooltip_label.pack()
            self._hover_item = None

        # Only rewrite the text when the hovered cell actually changed.
        if item != self._hover_item and self._tooltip_label is not None:
            self._hover_item = item
            self._tooltip_label.configure(
                text=f"Date:\n{date_str}\n\nStudy Time:\n{minutes_to_hm_text(total_minutes)}"
            )

        x = self.canvas.winfo_rootx() + event.x + 16
        y = self.canvas.winfo_rooty() + event.y + 16
        self._tooltip.wm_geometry(f"+{x}+{y}")
        self._tooltip.deiconify()

    def _hide_tooltip(self, event: tk.Event | None = None) -> None:
        self._hover_item = None
        if self._tooltip is not None:
            self._tooltip.withdraw()

    def destroy(self) -> None:
        if self._tooltip is not None:
            self._tooltip.destroy()
            self._tooltip = None
        super().destroy()

class AddLogFrame(tb.Frame):
    def __init__(self, parent, db, on_logs_changed=None):
        super().__init__(parent, padding=20)
        self.db = db
        self.on_logs_changed = on_logs_changed
        self.subject_docs = []  
        self.row_widgets = []  
        self._build_ui()
        self.refresh_subjects()
        self._refresh_stats()
        self.master.bind("<<NotebookTabChanged>>", self._on_tab_changed, add="+")

    # ------------------------------------------------------------------
    def _build_ui(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        title = tb.Label(self, text="Add Study Log", font=("Tahoma", 16, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        self._build_left_panel()
        self._build_right_panel()

    # ------------------------------------------------------------------
    def _build_left_panel(self):
        left = tb.Frame(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 15))
        left.columnconfigure(0, weight=1)

        # --- stats row ---
        stats_frame = tb.Frame(left)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        stats_frame.columnconfigure((0, 1, 2), weight=1)

        self.streak_label = tb.Label(
            stats_frame, text="", font=("Tahoma", 10, "bold"), bootstyle="warning"
        )
        self.streak_label.grid(row=0, column=0, sticky="w")

        self.week_label = tb.Label(
            stats_frame, text="", font=("Tahoma", 10), bootstyle="info"
        )
        self.week_label.grid(row=0, column=1)

        self.month_label = tb.Label(
            stats_frame, text="", font=("Tahoma", 10), bootstyle="success"
        )
        self.month_label.grid(row=0, column=2, sticky="e")

        current_year = datetime.now().year
        heatmap_card = tb.Labelframe(
            left, text=f"Study Activity ({current_year})", padding=12, bootstyle="primary"
        )
        heatmap_card.grid(row=1, column=0, sticky="nsew")
        heatmap_card.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        self.heatmap = StudyHeatmap(heatmap_card, self.db, on_day_click=self._on_heatmap_day_click)
        self.heatmap.grid(row=0, column=0, sticky="ew")

        hint = tb.Label(
            heatmap_card,
            text="Tip: click a day to load its date and see what was studied.",
            font=("Tahoma", 9), bootstyle="secondary"
        )
        hint.grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_right_panel(self):
        right = tb.Frame(self)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        # date row
        date_frame = tb.Frame(right)
        date_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        date_frame.columnconfigure(0, weight=1)

        tb.Label(date_frame, text="Date:", font=("Tahoma", 11)).grid(row=0, column=0, sticky="w")
        self.date_entry = tb.Entry(date_frame, font=("Tahoma", 11), width=15, justify="center", bootstyle="primary")
        self.date_entry.insert(0, today_str())
        self.date_entry.grid(row=0, column=1, sticky="e")

        # subject rows card
        card = tb.Labelframe(right, text="Subjects and Study Duration", padding=15, bootstyle="primary")
        card.grid(row=1, column=0, rowspan=2, sticky="nsew", pady=(0, 15))
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        # column headers
        header = tb.Frame(card)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(1, weight=1)

        tb.Label(header, text="Minutes", font=("Tahoma", 10, "bold")).grid(row=0, column=0, sticky="w")
        tb.Label(header, text="Subject", font=("Tahoma", 10, "bold")).grid(row=0, column=1, sticky="e")

        # scrollable area for subject rows
        scroll_container = tb.Frame(card)
        scroll_container.grid(row=1, column=0, sticky="nsew")
        scroll_container.columnconfigure(0, weight=1)
        scroll_container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(scroll_container, highlightthickness=0, bg="#222222")
        v_scroll = tb.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview, bootstyle="round")
        self.rows_frame = tb.Frame(self.canvas)

        self.rows_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        # submit button
        submit_btn = tb.Button(
            right, text="Save Today's Study Log", command=self.submit,
            bootstyle="success", width=22
        )
        submit_btn.grid(row=3, column=0, pady=(5, 5))

        self.status_label = tb.Label(right, text="", font=("Tahoma", 10), bootstyle="secondary")
        self.status_label.grid(row=4, column=0, pady=(5, 0))

    def refresh_subjects(self):
        for child in self.rows_frame.winfo_children():
            child.destroy()
        self.row_widgets.clear()

        self.subject_docs = self.db.get_subjects()
        rows_to_show = self.subject_docs

        if not rows_to_show:
            empty_label = tb.Label(
                self.rows_frame,
                text="No subjects yet. Add some from the 'Manage Subjects' tab first.",
                font=("Tahoma", 10), bootstyle="secondary"
            )
            empty_label.grid(row=0, column=0, pady=20, sticky="ew")
            return

        self.rows_frame.columnconfigure(1, weight=1)

        for i, doc in enumerate(rows_to_show):
            row = tb.Frame(self.rows_frame)
            row.grid(row=i, column=0, columnspan=2, sticky="ew", pady=4)
            row.columnconfigure(1, weight=1)

            minutes_var = tb.IntVar(value=0)
            spin = tb.Spinbox(
                row, from_=0, to=SPIN_MAX_MINUTES, increment=SPIN_STEP,
                textvariable=minutes_var, width=8, justify="center",
                bootstyle="primary"
            )
            spin.grid(row=0, column=0, sticky="w")

            name_label = tb.Label(row, text=doc["name"], font=("Tahoma", 11), anchor="e")
            name_label.grid(row=0, column=1, sticky="ew", padx=(10, 0))

            self.row_widgets.append({
                "subject_doc": doc,
                "minutes_var": minutes_var,
            })

    def _refresh_stats(self):
        streak = self.db.get_current_streak()
        week_total = self.db.get_week_total()
        month_total = self.db.get_month_total()

        self.streak_label.config(text=f"🔥 Streak: {streak} day{'s' if streak != 1 else ''}")
        self.week_label.config(text=f"This week: {minutes_to_hm_text(week_total)}")
        self.month_label.config(text=f"This month: {minutes_to_hm_text(month_total)}")

    def _refresh_all(self):
        self.heatmap.refresh()
        self._refresh_stats()

    def _on_tab_changed(self, event=None):
        try:
            current_tab = self.master.select()
            current_widget = self.master.nametowidget(current_tab)
        except Exception:
            return
        if current_widget is self:
            self._refresh_all()

    def _on_heatmap_day_click(self, date_str):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, date_str)

        logs = self.db.get_logs_by_date(date_str)
        if not logs:
            messagebox.showinfo("Day Details", f"No study records found for {date_str}.")
            return

        lines = [f"{log['subject_name']}: {minutes_to_hm_text(log['duration_minutes'])}" for log in logs]
        total = sum(log["duration_minutes"] for log in logs)
        lines.append(f"\nTotal: {minutes_to_hm_text(total)}")

        messagebox.showinfo("Day Details", f"{date_str}\n\n" + "\n".join(lines))

    # ------------------------------------------------------------------
    def submit(self):
        date_str = self.date_entry.get().strip()
        if not is_valid_date(date_str):
            messagebox.showerror("Error", "Enter the date in YYYY-MM-DD format. Example: 2026-06-29")
            return

        entries = []
        for row in self.row_widgets:
            try:
                minutes = int(row["minutes_var"].get())
            except Exception:
                minutes = 0
            if minutes > 0:
                entries.append({
                    "subject_id": row["subject_doc"]["_id"],
                    "subject_name": row["subject_doc"]["name"],
                    "duration_minutes": minutes,
                })

        if not entries:
            messagebox.showinfo("Notice", "You didn't enter any time for any subject.")
            return

        count = self.db.add_logs_bulk(date_str, entries)

        total_minutes = sum(e["duration_minutes"] for e in entries)
        summary_lines = [f"{e['subject_name']}: {minutes_to_hm_text(e['duration_minutes'])}" for e in entries]
        summary_text = "\n".join(summary_lines)

        self.status_label.config(
            text=f"{count} subjects saved for {date_str}. Total: {minutes_to_hm_text(total_minutes)}"
        )
        messagebox.showinfo("Saved", f"The following was saved:\n\n{summary_text}")

        for row in self.row_widgets:
            row["minutes_var"].set(0)

        self._refresh_all()
        if self.on_logs_changed:
            self.on_logs_changed()