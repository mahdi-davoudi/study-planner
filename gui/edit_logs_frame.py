import ttkbootstrap as tb
from tkinter import messagebox
from utils.helpers import today_str, is_valid_date, minutes_to_hm_text

SPIN_MAX_MINUTES = 240
SPIN_STEP = 5


class EditLogsFrame(tb.Frame):
    def __init__(self, parent, db, on_logs_changed=None):
        super().__init__(parent, padding=20)
        self.db = db
        self.on_logs_changed = on_logs_changed
        self._logs = []

        self._build_ui()
        self.load_logs()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        title = tb.Label(self, text="Edit / Delete Saved Records", font=("Tahoma", 16, "bold"))
        title.grid(row=0, column=0, sticky="e", pady=(0, 15))

        # --- date selection bar ---
        controls = tb.Frame(self)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        controls.columnconfigure(0, weight=1)

        load_btn = tb.Button(controls, text="Show Records for This Day", command=self.load_logs, bootstyle="info")
        load_btn.grid(row=0, column=2, padx=(8, 0))

        self.date_entry = tb.Entry(controls, font=("Tahoma", 11), width=15, justify="center", bootstyle="primary")
        self.date_entry.insert(0, today_str())
        self.date_entry.grid(row=0, column=1)
        self.date_entry.bind("<Return>", lambda e: self.load_logs())

        tb.Label(controls, text="Date:", font=("Tahoma", 11)).grid(row=0, column=0, sticky="e")

        # --- records table card ---
        table_card = tb.Labelframe(self, text="Records for Selected Day", padding=10, bootstyle="primary")
        table_card.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(0, weight=1)

        self.tree = tb.Treeview(
            table_card, columns=("subject", "time"), show="headings",
            height=12, bootstyle="primary"
        )
        self.tree.heading("subject", text="Subject")
        self.tree.heading("time", text="Study Time")
        self.tree.column("subject", anchor="e", width=220)
        self.tree.column("time", anchor="center", width=160)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = tb.Scrollbar(table_card, orient="vertical", command=self.tree.yview, bootstyle="round")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        # --- action buttons ---
        action_frame = tb.Frame(self)
        action_frame.grid(row=3, column=0, sticky="e")

        delete_btn = tb.Button(action_frame, text="Delete Selected Record", command=self.delete_selected, bootstyle="danger")
        delete_btn.grid(row=0, column=1, padx=(8, 0))

        edit_btn = tb.Button(action_frame, text="Edit Time", command=self.edit_selected, bootstyle="warning")
        edit_btn.grid(row=0, column=0)

        hint = tb.Label(
            self, text="Tip: double-click a row to edit it directly.",
            font=("Tahoma", 9), bootstyle="secondary"
        )
        hint.grid(row=4, column=0, sticky="e", pady=(10, 0))

    # ------------------------------------------------------------------
    def load_logs(self):
        """Read the records for the selected date from the database and display them in the table."""
        date_str = self.date_entry.get().strip()
        if not is_valid_date(date_str):
            messagebox.showerror("Error", "Enter the date in YYYY-MM-DD format.")
            return

        self._logs = self.db.get_logs_by_date(date_str)

        for row in self.tree.get_children():
            self.tree.delete(row)

        for log in self._logs:
            self.tree.insert("", "end", iid=str(log["_id"]), values=(
                log["subject_name"],
                minutes_to_hm_text(log["duration_minutes"])
            ))

        if not self._logs:
            messagebox.showinfo("Notice", f"No records found for {date_str}.")

    def _get_selected_log(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Notice", "Select a record from the table first.")
            return None
        selected_id = selection[0]
        for log in self._logs:
            if str(log["_id"]) == selected_id:
                return log
        return None

    def delete_selected(self):
        log = self._get_selected_log()
        if not log:
            return
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete the record '{log['subject_name']} - {minutes_to_hm_text(log['duration_minutes'])}'?"
        )
        if confirm:
            self.db.delete_log(log["_id"])
            self.load_logs()
            if self.on_logs_changed:
                self.on_logs_changed()

    def edit_selected(self):
        log = self._get_selected_log()
        if not log:
            return

        dialog = tb.Toplevel(self)
        dialog.title("Edit Study Time")
        dialog.geometry("300x180")
        dialog.resizable(False, False)

        tb.Label(
            dialog, text=f"Subject: {log['subject_name']}", font=("Tahoma", 11, "bold")
        ).pack(pady=(20, 10))

        minutes_var = tb.IntVar(value=log["duration_minutes"])
        spin = tb.Spinbox(
            dialog, from_=0, to=SPIN_MAX_MINUTES, increment=SPIN_STEP,
            textvariable=minutes_var, width=10, justify="center",
            bootstyle="primary"
        )
        spin.pack(pady=5)

        tb.Label(dialog, text="(value in minutes)", font=("Tahoma", 9), bootstyle="secondary").pack()

        def save():
            try:
                new_minutes = int(minutes_var.get())
            except Exception:
                new_minutes = 0
            if new_minutes <= 0:
                messagebox.showwarning("Error", "The entered time must be greater than zero.")
                return
            self.db.update_log_duration(log["_id"], new_minutes)
            dialog.destroy()
            self.load_logs()
            if self.on_logs_changed:
                self.on_logs_changed()

        tb.Button(dialog, text="Save", command=save, bootstyle="success").pack(pady=15)
        dialog.bind("<Return>", lambda e: save())