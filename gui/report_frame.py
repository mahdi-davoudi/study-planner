import ttkbootstrap as tb
from tkinter import messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.helpers import today_str, is_valid_date, minutes_to_hm_text

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def _fix_rtl(text: str) -> str:
        """
        matplotlib does not perform Arabic/Persian text shaping or
        bidi reordering on its own, so Persian subject names render
        with disconnected/reversed letters. Reshape + reorder here so
        they display correctly in the chart legend.
        """
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text
except ImportError:
    def _fix_rtl(text: str) -> str:
        return text

# Dark, ttkbootstrap-"darkly" friendly chart colors
CHART_BG = "#222222"
CHART_TEXT = "#e6edf3"
SLICE_COLORS = [
    "#39d353", "#58a6ff", "#f0ad4e", "#e05780", "#a78bfa",
    "#2dd4bf", "#f97316", "#facc15", "#60a5fa", "#f472b6",
    "#4ade80", "#c084fc",
]


class ReportFrame(tb.Frame):

    def __init__(self, parent, db):
        super().__init__(parent, padding=15)

        self.db = db

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.build_ui()

    # -------------------------------------------------------------

    def build_ui(self):

        ##########################################################
        # Title
        ##########################################################

        title = tb.Label(
            self,
            text="Study Report",
            font=("Segoe UI", 18, "bold")
        )

        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        ##########################################################
        # Date Range Card
        ##########################################################

        controls = tb.Labelframe(
            self,
            text="Date Range",
            padding=15,
            bootstyle="primary"
        )

        controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))

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

        ##########################################################
        # Center: Donut Chart (left) + Table (right)
        ##########################################################

        chart_frame = tb.Labelframe(
            self,
            text="Study Distribution",
            padding=10,
            bootstyle="primary"
        )

        chart_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(4.2, 4.2), dpi=100, facecolor=CHART_BG)
        self.ax = self.figure.add_subplot(111)

        self.chart_canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        result_frame = tb.Labelframe(
            self,
            text="Results",
            padding=10,
            bootstyle="primary"
        )

        result_frame.grid(
            row=2,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.tree = tb.Treeview(
            result_frame,
            columns=("subject", "time", "percentage"),
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

        self.tree.heading(
            "percentage",
            text="Percentage"
        )

        self.tree.column(
            "subject",
            anchor="center",
            width=200
        )

        self.tree.column(
            "time",
            anchor="center",
            width=160
        )

        self.tree.column(
            "percentage",
            anchor="center",
            width=100
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

        ##########################################################
        # Total Label
        ##########################################################

        self.total_label = tb.Label(
            self,
            text="",
            font=("Segoe UI", 11, "bold"),
            bootstyle="success"
        )

        self.total_label.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(10, 0)
        )

        self.show_range_summary()

    # -------------------------------------------------------------

    def clear_table(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

    # -------------------------------------------------------------

    def _render_table(self, summary):
        """
        Populate the results table from a list of
        {subject_name, total_minutes, percentage} dicts.
        The donut chart is controlled separately - see
        _show_alltime_donut() / _show_today_donut().
        """
        self.clear_table()

        if not summary:
            self.total_label.config(text="No study records found.")
            return

        total = 0

        for item in summary:
            self.tree.insert(
                "",
                "end",
                values=(
                    item["subject_name"],
                    minutes_to_hm_text(item["total_minutes"]),
                    f"{item['percentage']:.1f}%"
                )
            )
            total += item["total_minutes"]

        self.total_label.config(
            text=f"Total Study Time : {minutes_to_hm_text(total)}"
        )

    # -------------------------------------------------------------

    def _show_alltime_donut(self):
        """
        The donut chart's default/persistent state: total study time
        across all recorded history, regardless of the date range
        selected for the table.
        """
        summary = self.db.get_subject_percentages()
        total = sum(item["total_minutes"] for item in summary)
        self._draw_donut(summary, total)

    def _show_today_donut(self):
        """Switch the donut chart to show only today's study time."""
        today = today_str()
        summary = self.db.get_subject_percentages(today, today)
        total = sum(item["total_minutes"] for item in summary)
        self._draw_donut(summary, total)

    # -------------------------------------------------------------

    def _draw_donut(self, summary, total_minutes):
        self.ax.clear()
        self.figure.set_facecolor(CHART_BG)
        self.ax.set_facecolor(CHART_BG)

        if not summary or total_minutes <= 0:
            self.ax.text(
                0.5, 0.5, "No data",
                ha="center", va="center", color=CHART_TEXT, fontsize=12,
                transform=self.ax.transAxes
            )
            self.ax.axis("off")
            self.chart_canvas.draw()
            return

        labels = [_fix_rtl(item["subject_name"]) for item in summary]
        sizes = [item["total_minutes"] for item in summary]
        colors = [SLICE_COLORS[i % len(SLICE_COLORS)] for i in range(len(summary))]

        wedges, _texts, autotexts = self.ax.pie(
            sizes,
            colors=colors,
            autopct="%1.1f%%",
            pctdistance=0.82,
            startangle=90,
            wedgeprops={"width": 0.42, "edgecolor": CHART_BG, "linewidth": 2},
            textprops={"color": CHART_BG, "fontsize": 8, "weight": "bold"},
        )

        hours = total_minutes // 60
        minutes = total_minutes % 60
        center_text = f"{hours}h {minutes}m" if hours else f"{minutes}m"

        self.ax.text(
            0, 0.08, center_text,
            ha="center", va="center", color=CHART_TEXT,
            fontsize=15, fontweight="bold"
        )
        self.ax.text(
            0, -0.12, "Total",
            ha="center", va="center", color="#8b949e", fontsize=9
        )

        self.ax.legend(
            wedges, labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.02),
            ncol=2,
            frameon=False,
            fontsize=8,
            labelcolor=CHART_TEXT,
        )

        self.ax.axis("equal")
        self.figure.tight_layout()
        self.chart_canvas.draw()

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

        summary = self.db.get_subject_percentages(start, end)
        self._render_table(summary)
        self._show_alltime_donut()

    # -------------------------------------------------------------

    def show_day_detail(self):

        date = self.start_date_entry.get().strip()

        if not is_valid_date(date):

            messagebox.showerror(
                "Error",
                "Date format must be YYYY-MM-DD."
            )

            return

        summary = self.db.get_subject_percentages(date, date)
        self._render_table(summary)
        self._show_today_donut()