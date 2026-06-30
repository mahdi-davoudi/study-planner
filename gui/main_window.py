import ttkbootstrap as tb
from gui.add_log_frame import AddLogFrame
from gui.manage_subjects_frame import ManageSubjectsFrame
from gui.report_frame import ReportFrame
from gui.edit_logs_frame import EditLogsFrame


DARK_THEME = "darkly"


class MainWindow(tb.Window):
    def __init__(self, db):
        super().__init__(themename=DARK_THEME)

        self.db = db

        self.title("Study Planner")

        # ---------- Window Size ----------
        window_width = 1100
        window_height = 700

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(900, 600)

        # ---------- Optional Icon ----------
        try:
            self.iconbitmap("assets/icons/icon.ico")
        except Exception:
            pass

        self._build_ui()

        # Focus on the main window
        self.focus_force()

    # --------------------------------------------------

    def _build_ui(self):

        # Main Notebook
        self.notebook = tb.Notebook(
            self,
            bootstyle="dark"
        )

        self.notebook.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )

        # ---------------- Pages ----------------

        self.add_log_frame = AddLogFrame(
            self.notebook,
            self.db
        )

        self.manage_subjects_frame = ManageSubjectsFrame(
            self.notebook,
            self.db,
            on_subjects_changed=self._on_subjects_changed
        )

        self.report_frame = ReportFrame(
            self.notebook,
            self.db
        )

        self.edit_logs_frame = EditLogsFrame(
            self.notebook,
            self.db,
            on_logs_changed=self._on_logs_changed
        )

        # ---------------- Tabs ----------------

        self.notebook.add(
            self.add_log_frame,
            text="📝 Add Study"
        )

        self.notebook.add(
            self.manage_subjects_frame,
            text="📚 Subjects"
        )

        self.notebook.add(
            self.report_frame,
            text="📊 Reports"
        )

        self.notebook.add(
            self.edit_logs_frame,
            text="✏ Edit Logs"
        )

        # Open first tab by default
        self.notebook.select(0)

    # --------------------------------------------------

    def _on_subjects_changed(self):
        """
        Refresh the subject list in Add Study tab
        after a subject is added/edited/deleted.
        """
        self.add_log_frame.refresh_subjects()

    # --------------------------------------------------

    def _on_logs_changed(self):
        """
        Refresh report after editing/deleting logs.
        """
        self.report_frame.show_range_summary()