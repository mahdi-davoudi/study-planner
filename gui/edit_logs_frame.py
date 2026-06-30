import tkinter as tk
from tkinter import ttk, messagebox

from utils.helpers import today_str, is_valid_date, minutes_to_hm_text, hm_to_minutes


class EditLogsFrame(ttk.Frame):
    def __init__(self, parent, db, on_logs_changed=None):
        super().__init__(parent, padding=15)
        self.db = db
        self.on_logs_changed = on_logs_changed
        self._logs = [] 

        self._build_ui()
        self.load_logs()

    def _build_ui(self):
        title = ttk.Label(self, text="edit/ remove files", font=("Tahoma", 14, "bold"))
        title.pack(anchor="e", pady=(0, 10))

        # --- نوار انتخاب تاریخ ---
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="date (YYYY-MM-DD):", font=("Tahoma", 11)).pack(side="right")
        self.date_entry = ttk.Entry(controls, font=("Tahoma", 11), width=15, justify="center")
        self.date_entry.insert(0, today_str())
        self.date_entry.pack(side="right", padx=(0, 8))
        self.date_entry.bind("<Return>", lambda e: self.load_logs())

        load_btn = ttk.Button(controls, text="Show records for this day", command=self.load_logs)
        load_btn.pack(side="right")

        # --- جدول رکوردها ---
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, pady=(5, 0))

        self.tree = ttk.Treeview(
            table_frame, columns=("subject", "time"), show="headings", height=12
        )
        self.tree.heading("subject", text="lesson")
        self.tree.heading("time", text="study time")
        self.tree.column("subject", anchor="e", width=220)
        self.tree.column("time", anchor="center", width=160)
        self.tree.pack(side="right", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="left", fill="y")
        self.tree.config(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        # --- دکمه‌های عملیات ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", pady=(10, 0))

        delete_btn = ttk.Button(action_frame, text="Delete selected record", command=self.delete_selected)
        delete_btn.pack(side="right", padx=(5, 0))

        edit_btn = ttk.Button(action_frame, text="edit time", command=self.edit_selected)
        edit_btn.pack(side="right")

        hint = ttk.Label(
            self, text="Tip: Double-click a row to edit it directly.",
            font=("Tahoma", 9), foreground="gray"
        )
        hint.pack(anchor="e", pady=(8, 0))

    # ------------------------------------------------------------------
    def load_logs(self):
        date_str = self.date_entry.get().strip()
        if not is_valid_date(date_str):
            messagebox.showerror("error", "add date like YYYY-MM-DD .")
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
            messagebox.showinfo("attention", f"for {date_str} no record")

    def _get_selected_log(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("attention", "first, chose a record from the table.")
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
            "Confirm deletion",
            f"delete «{log['subject_name']} - {minutes_to_hm_text(log['duration_minutes'])}» record?"
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

        current_hours = log["duration_minutes"] // 60
        current_minutes = log["duration_minutes"] % 60

        dialog = tk.Toplevel(self)
        dialog.title("edit study time")
        dialog.geometry("280x160")
        dialog.resizable(False, False)

        ttk.Label(
            dialog, text=f"lesson: {log['subject_name']}", font=("Tahoma", 11, "bold")
        ).pack(pady=(15, 10))

        input_frame = ttk.Frame(dialog)
        input_frame.pack()

        ttk.Label(input_frame, text="hour:", font=("Tahoma", 10)).pack(side="right", padx=4)
        hour_entry = ttk.Entry(input_frame, width=6, justify="center")
        hour_entry.insert(0, str(current_hours))
        hour_entry.pack(side="right", padx=4)

        ttk.Label(input_frame, text="minute:", font=("Tahoma", 10)).pack(side="right", padx=4)
        min_entry = ttk.Entry(input_frame, width=6, justify="center")
        min_entry.insert(0, str(current_minutes))
        min_entry.pack(side="right", padx=4)

        hour_entry.focus()

        def save():
            new_minutes = hm_to_minutes(hour_entry.get(), min_entry.get())
            if new_minutes <= 0:
                messagebox.showwarning("error", "The time entered must be greater than zero.")
                return
            self.db.update_log_duration(log["_id"], new_minutes)
            dialog.destroy()
            self.load_logs()
            if self.on_logs_changed:
                self.on_logs_changed()

        ttk.Button(dialog, text="save", command=save).pack(pady=15)
        dialog.bind("<Return>", lambda e: save())