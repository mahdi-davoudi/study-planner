import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from config import MAX_SUBJECT_ROWS
from utils.helpers import today_str, is_valid_date, minutes_to_hm_text

SPIN_MAX_MINUTES = 240   # max 4 hours per subject in a single Spinbox
SPIN_STEP = 5             # 5-minute increments


class AddLogFrame(tb.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=20)
        self.db = db
        self.subject_docs = []   # list of subject documents from the database
        self.row_widgets = []    # each item: dict with subject_doc, minutes_var

        self._build_ui()
        self.refresh_subjects()

    # ------------------------------------------------------------------
    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        title = tb.Label(self, text="Add Study Log", font=("Tahoma", 16, "bold"))
        title.grid(row=0, column=0, sticky="e", pady=(0, 15))

        # --- date row ---
        date_frame = tb.Frame(self)
        date_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        date_frame.columnconfigure(0, weight=1)

        tb.Label(date_frame, text="Date:", font=("Tahoma", 11)).grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.date_entry = tb.Entry(date_frame, font=("Tahoma", 11), width=15, justify="center", bootstyle="primary")
        self.date_entry.insert(0, today_str())
        self.date_entry.grid(row=0, column=1, sticky="e")

        # --- subject rows card ---
        card = tb.Labelframe(self, text="Subjects and Study Duration", padding=15, bootstyle="primary")
        card.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        card.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # column headers
        header = tb.Frame(card)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)

        tb.Label(header, text="Subject", font=("Tahoma", 10, "bold")).grid(row=0, column=1, sticky="e")
        tb.Label(header, text="Minutes", font=("Tahoma", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))

        # scrollable area for subject rows
        scroll_container = tb.Frame(card)
        scroll_container.grid(row=1, column=0, sticky="nsew")
        card.rowconfigure(1, weight=1)
        scroll_container.columnconfigure(0, weight=1)

        self.canvas = tb.Canvas(scroll_container, highlightthickness=0, height=260)
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

        # --- submit button ---
        submit_btn = tb.Button(
            self, text="Save Today's Study Log", command=self.submit,
            bootstyle="success", width=22
        )
        submit_btn.grid(row=3, column=0, pady=(5, 5))

        self.status_label = tb.Label(self, text="", font=("Tahoma", 10), bootstyle="secondary")
        self.status_label.grid(row=4, column=0, pady=(5, 0))

    # ------------------------------------------------------------------
    def refresh_subjects(self):
        """
        Reload the subject list from the database and rebuild the form rows.
        Up to MAX_SUBJECT_ROWS rows are shown (fewer if fewer subjects exist).
        """
        for child in self.rows_frame.winfo_children():
            child.destroy()
        self.row_widgets.clear()

        self.subject_docs = self.db.get_subjects()
        rows_to_show = self.subject_docs[:MAX_SUBJECT_ROWS]

        if not rows_to_show:
            empty_label = tb.Label(
                self.rows_frame,
                text="No subjects yet. Add some from the 'Manage Subjects' tab first.",
                font=("Tahoma", 10), bootstyle="secondary"
            )
            empty_label.grid(row=0, column=0, pady=20, sticky="ew")
            return

        self.rows_frame.columnconfigure(0, weight=1)

        for i, doc in enumerate(rows_to_show):
            row = tb.Frame(self.rows_frame)
            row.grid(row=i, column=0, sticky="ew", pady=4)
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