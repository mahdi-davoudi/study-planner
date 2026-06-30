import tkinter as tk
from tkinter import ttk, messagebox

from config import MAX_SUBJECT_ROWS
from utils.helpers import today_str, is_valid_date, hm_to_minutes, minutes_to_hm_text


class AddLogFrame(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)
        self.db = db
        self.subject_docs = []   # لیست اسناد درس از دیتابیس
        self.row_widgets = []    # هر آیتم: dict با subject_doc, hour_entry, min_entry

        self._build_ui()
        self.refresh_subjects()

    # ------------------------------------------------------------------
    def _build_ui(self):
        title = ttk.Label(self, text="Daily Study Record", font=("Tahoma", 14, "bold"))
        title.pack(anchor="e", pady=(0, 10))

        # --- date row ---
        date_frame = ttk.Frame(self)
        date_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(date_frame, text="Date (YYYY-MM-DD):", font=("Tahoma", 11)).pack(side="right")
        self.date_entry = ttk.Entry(date_frame, font=("Tahoma", 11), width=15, justify="center")
        self.date_entry.insert(0, today_str())
        self.date_entry.pack(side="right", padx=(0, 8))

        # fixed pixel widths for columns (header and rows both use these so they align exactly)
        self.COL_NAME_WIDTH = 220
        self.COL_BOX_WIDTH = 70

        # --- column headers (using grid, so they line up exactly with the rows) ---
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(5, 2))

        name_header = ttk.Label(header, text="Lesson", font=("Tahoma", 10, "bold"), anchor="e")
        name_header.grid(row=0, column=2, sticky="ew")

        hour_header = ttk.Label(header, text="Hour", font=("Tahoma", 10, "bold"), anchor="center")
        hour_header.grid(row=0, column=1, sticky="ew", padx=2)

        min_header = ttk.Label(header, text="Minute", font=("Tahoma", 10, "bold"), anchor="center")
        min_header.grid(row=0, column=0, sticky="ew", padx=2)

        # lock header column widths to fixed pixel sizes
        header.grid_columnconfigure(0, minsize=self.COL_BOX_WIDTH)
        header.grid_columnconfigure(1, minsize=self.COL_BOX_WIDTH)
        header.grid_columnconfigure(2, minsize=self.COL_NAME_WIDTH)

        # --- scrollable area for lesson rows ---
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.rows_frame = ttk.Frame(canvas)

        self.rows_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        # --- submit button ---
        submit_btn = ttk.Button(self, text="Add Today's Study", command=self.submit)
        submit_btn.pack(pady=(10, 0))

        self.status_label = ttk.Label(self, text="", font=("Tahoma", 10))
        self.status_label.pack(pady=(5, 0))
    # ------------------------------------------------------------------
    def refresh_subjects(self):
        # پاک کردن ردیف‌های قبلی
        for child in self.rows_frame.winfo_children():
            child.destroy()
        self.row_widgets.clear()

        self.subject_docs = self.db.get_subjects()
        rows_to_show = self.subject_docs[:MAX_SUBJECT_ROWS]

        if not rows_to_show:
            empty_label = ttk.Label(
                self.rows_frame,
                text="No lessons yet. Add some from the 'manage lessons' tab first.",
                font=("Tahoma", 10), foreground="gray"
            )
            empty_label.pack(pady=20)
            return

        for doc in rows_to_show:
            row = ttk.Frame(self.rows_frame)
            row.pack(fill="x", pady=3)

            # same three columns via grid, matching the header's pixel widths
            row.grid_columnconfigure(0, minsize=self.COL_BOX_WIDTH)
            row.grid_columnconfigure(1, minsize=self.COL_BOX_WIDTH)
            row.grid_columnconfigure(2, minsize=self.COL_NAME_WIDTH)

            name_label = ttk.Label(row, text=doc["name"], font=("Tahoma", 11), anchor="e")
            name_label.grid(row=0, column=2, sticky="ew")

            hour_entry = ttk.Entry(row, width=8, justify="center")
            hour_entry.grid(row=0, column=1, padx=2)
            hour_entry.insert(0, "0")

            min_entry = ttk.Entry(row, width=8, justify="center")
            min_entry.grid(row=0, column=0, padx=2)
            min_entry.insert(0, "0")

            self.row_widgets.append({
                "subject_doc": doc,
                "hour_entry": hour_entry,
                "min_entry": min_entry,
            })
    # ------------------------------------------------------------------
    def submit(self):
        date_str = self.date_entry.get().strip()
        if not is_valid_date(date_str):
            messagebox.showerror("error", "add date like YYYY-MM-DD for example: 2026-06-29")
            return

        entries = []
        for row in self.row_widgets:
            minutes = hm_to_minutes(row["hour_entry"].get(), row["min_entry"].get())
            if minutes > 0:
                entries.append({
                    "subject_id": row["subject_doc"]["_id"],
                    "subject_name": row["subject_doc"]["name"],
                    "duration_minutes": minutes,
                })

        if not entries:
            messagebox.showinfo("Attention", "You never entered any time for any lesson.")
            return

        count = self.db.add_logs_bulk(date_str, entries)

        # خلاصه‌ای از چیزی که ثبت شد را نشان بده
        total_minutes = sum(e["duration_minutes"] for e in entries)
        summary_lines = [f"{e['subject_name']}: {minutes_to_hm_text(e['duration_minutes'])}" for e in entries]
        summary_text = "\n".join(summary_lines)

        self.status_label.config(
            text=f"in total {count} lesson for date {date_str} added {minutes_to_hm_text(total_minutes)}"
        )
        messagebox.showinfo("Registered", f"The following were recorded::\n\n{summary_text}")

        # ریست کردن مقادیر فرم برای ثبت روز بعدی
        for row in self.row_widgets:
            row["hour_entry"].delete(0, tk.END)
            row["hour_entry"].insert(0, "0")
            row["min_entry"].delete(0, tk.END)
            row["min_entry"].insert(0, "0")