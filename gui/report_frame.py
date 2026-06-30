import ttkbootstrap as tb
from tkinter import messagebox
from utils.helpers import today_str, is_valid_date, minutes_to_hm_text


class ReportFrame(tb.Frame):

    def __init__(self, parent, db):
        super().__init__(parent, padding=15)

        self.db = db

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.build_ui()

    # -------------------------------------------------------------

    def build_ui(self):

        ############################################################
        # Title
        ############################################################

        title = tb.Label(
            self,
            text="Study Report",
            font=("Segoe UI", 18, "bold")
        )

        title.grid(row=0, column=0, sticky="w", pady=(0, 15))

        ############################################################
        # Date Range Card
        ############################################################

        controls = tb.Labelframe(
            self,
            text="Date Range",
            padding=15,
            bootstyle="primary"
        )

        controls.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        controls.columnconfigure(8, weight=1)

        tb.Label(
            controls,
            text="From"
        ).grid(row=0, column=0, padx=(0, 5))

        self.start_date_entry = tb.Entry(
            controls,
            width=14,
            justify="center"
        )

        self.start_date_entry.insert(0, today_str())

        self.start_date_entry.grid(
            row=0,
            column=1,
            padx=(0, 20)
        )

        tb.Label(
            controls,
            text="To"
        ).grid(
            row=0,
            column=2,
            padx=(0, 5)
        )

        self.end_date_entry = tb.Entry(
            controls,
            width=14,
            justify="center"
        )

        self.end_date_entry.insert(0, today_str())

        self.end_date_entry.grid(
            row=0,
            column=3,
            padx=(0, 40)
        )

        tb.Button(
            controls,
            text="Show Day Details",
            command=self.show_day_detail,
            bootstyle="secondary"
        ).grid(row=0, column=4, padx=5)

        tb.Button(
            controls,
            text="Show Range Summary",
            command=self.show_range_summary,
            bootstyle="success"
        ).grid(row=0, column=5)

        ############################################################
        # Results
        ############################################################

        result_frame = tb.Labelframe(
            self,
            text="Results",
            padding=10,
            bootstyle="primary"
        )

        result_frame.grid(
            row=2,
            column=0,
            sticky="nsew"
        )

        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.tree = tb.Treeview(
            result_frame,
            columns=("subject", "time"),
            show="headings",
            bootstyle="primary"
        )

        self.tree.heading(
            "subject",
            text="Subject"
        )

        self.tree.heading(
            "time",
            text="Study Time"
        )

        self.tree.column(
            "subject",
            anchor="center",
            width=400
        )

        self.tree.column(
            "time",
            anchor="center",
            width=200
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar = tb.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="round"
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        ############################################################
        # Total Label
        ############################################################

        self.total_label = tb.Label(
            self,
            text="",
            font=("Segoe UI", 11, "bold"),
            bootstyle="success"
        )

        self.total_label.grid(
            row=3,
            column=0,
            sticky="e",
            pady=(10, 0)
        )

        self.show_range_summary()

    # -------------------------------------------------------------

    def clear_table(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

    # -------------------------------------------------------------

    def show_range_summary(self):

        start = self.start_date_entry.get().strip()
        end = self.end_date_entry.get().strip()

        if not is_valid_date(start) or not is_valid_date(end):
            messagebox.showerror(
                "Error",
                "Date format must be YYYY-MM-DD."
            )
            return

        if start > end:
            messagebox.showerror(
                "Error",
                "Start date must be before end date."
            )
            return

        summary = self.db.get_summary_by_subject(
            start,
            end
        )

        self.clear_table()

        if not summary:

            self.total_label.config(
                text="No study records found."
            )

            return

        total = 0

        for item in summary:

            self.tree.insert(
                "",
                "end",
                values=(
                    item["subject_name"],
                    minutes_to_hm_text(item["total_minutes"])
                )
            )

            total += item["total_minutes"]

        self.total_label.config(
            text=f"Total Study Time : {minutes_to_hm_text(total)}"
        )

    # -------------------------------------------------------------

    def show_day_detail(self):

        date = self.start_date_entry.get().strip()

        if not is_valid_date(date):

            messagebox.showerror(
                "Error",
                "Date format must be YYYY-MM-DD."
            )

            return

        logs = self.db.get_logs_by_date(date)

        self.clear_table()

        if not logs:

            self.total_label.config(
                text="No study records found."
            )

            return

        total = 0

        for log in logs:

            self.tree.insert(
                "",
                "end",
                values=(
                    log["subject_name"],
                    minutes_to_hm_text(log["duration_minutes"])
                )
            )

            total += log["duration_minutes"]

        self.total_label.config(
            text=f"Total Study Time : {minutes_to_hm_text(total)}"
        )