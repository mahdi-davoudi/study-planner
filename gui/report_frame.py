import tkinter as tk
from tkinter import ttk, messagebox

from utils.helpers import today_str, is_valid_date, minutes_to_hm_text


class ReportFrame(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(self, text="study report", font=("Tahoma", 14, "bold"))
        title.pack(anchor="e", pady=(0, 10))

        # --- نوار کنترل بازه زمانی ---
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="until: ", font=("Tahoma", 10)).pack(side="right")
        self.end_date_entry = ttk.Entry(controls, width=13, justify="center")
        self.end_date_entry.insert(0, today_str())
        self.end_date_entry.pack(side="right", padx=(4, 10))

        ttk.Label(controls, text="from: ", font=("Tahoma", 10)).pack(side="right")
        self.start_date_entry = ttk.Entry(controls, width=13, justify="center")
        self.start_date_entry.insert(0, today_str())
        self.start_date_entry.pack(side="right", padx=4)

        show_range_btn = ttk.Button(controls, text="Show interval sum", command=self.show_range_summary)
        show_range_btn.pack(side="right", padx=(10, 0))

        show_day_btn = ttk.Button(controls, text="Show details of a day", command=self.show_day_detail)
        show_day_btn.pack(side="right", padx=(5, 0))

        # --- جدول نتایج ---
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, pady=(5, 0))

        self.tree = ttk.Treeview(table_frame, columns=("subject", "time"), show="headings", height=15)
        self.tree.heading("subject", text="Lesson")
        self.tree.heading("time", text="study time")
        self.tree.column("subject", anchor="e", width=220)
        self.tree.column("time", anchor="center", width=160)
        self.tree.pack(side="right", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="left", fill="y")
        self.tree.config(yscrollcommand=scrollbar.set)

        # --- ردیف جمع کل ---
        self.total_label = ttk.Label(self, text="", font=("Tahoma", 11, "bold"))
        self.total_label.pack(pady=(8, 0), anchor="e")

        # نمایش پیش‌فرض: جمع امروز
        self.show_range_summary()

    # ------------------------------------------------------------------
    def _clear_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def show_range_summary(self):
        start = self.start_date_entry.get().strip()
        end = self.end_date_entry.get().strip()

        if not is_valid_date(start) or not is_valid_date(end):
            messagebox.showerror("error", "add date like YYYY-MM-DD .")
            return
        if start > end:
            messagebox.showerror("error", "The start date must be before the end date.")
            return

        summary = self.db.get_summary_by_subject(start, end)
        self._clear_table()

        if not summary:
            self.total_label.config(text="No studies have been recorded in this period.")
            return

        total = 0
        for item in summary:
            self.tree.insert("", "end", values=(
                item["subject_name"],
                minutes_to_hm_text(item["total_minutes"])
            ))
            total += item["total_minutes"]

        self.total_label.config(text=f"total sum ({start} to {end}): {minutes_to_hm_text(total)}")

    def show_day_detail(self):
        date_str = self.start_date_entry.get().strip()
        if not is_valid_date(date_str):
            messagebox.showerror("error", "add date like YYYY-MM-DD .")
            return

        logs = self.db.get_logs_by_date(date_str)
        self._clear_table()

        if not logs:
            self.total_label.config(text=f"in {date_str} No studies have been registered.")
            return

        total = 0
        for log in logs:
            self.tree.insert("", "end", values=(
                log["subject_name"],
                minutes_to_hm_text(log["duration_minutes"])
            ))
            total += log["duration_minutes"]

        self.total_label.config(text=f"the study of the day {date_str}: {minutes_to_hm_text(total)}")