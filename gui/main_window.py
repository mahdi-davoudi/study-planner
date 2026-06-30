import tkinter as tk
from tkinter import ttk

from gui.add_log_frame import AddLogFrame
from gui.manage_subjects_frame import ManageSubjectsFrame
from gui.report_frame import ReportFrame
from gui.edit_logs_frame import EditLogsFrame


class MainWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.title("Course Study Planning")
        self.geometry("650x550")
        self.minsize(550, 450)

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.add_log_frame = AddLogFrame(notebook, self.db)
        self.manage_subjects_frame = ManageSubjectsFrame(
            notebook, self.db, on_subjects_changed=self._on_subjects_changed
        )
        self.report_frame = ReportFrame(notebook, self.db)
        self.edit_logs_frame = EditLogsFrame(
            notebook, self.db, on_logs_changed=self._on_logs_changed
        )
        notebook.add(self.add_log_frame, text="Study registration")
        notebook.add(self.manage_subjects_frame, text="manage lessons")
        notebook.add(self.report_frame, text="report")
        notebook.add(self.edit_logs_frame, text="edit/delete")

    def _on_subjects_changed(self):
        self.add_log_frame.refresh_subjects()
    
    def _on_logs_changed(self):
        self.report_frame.show_range_summary()