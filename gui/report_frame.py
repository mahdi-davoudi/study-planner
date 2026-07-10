import ttkbootstrap as tb
from tkinter import messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.helpers import today_str, is_valid_date, minutes_to_hm_text

# Optional ttkbootstrap DateEntry - fall back to a plain Entry if the installed ttkbootstrap version does not ship it.
try:
    from ttkbootstrap.widgets import DateEntry
    HAS_DATEENTRY = True
except ImportError:
    HAS_DATEENTRY = False

# Optional Arabic/Persian shaping for the chart legend.
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def _fix_rtl(text: str) -> str:
        """
        matplotlib does not perform Arabic/Persian text shaping or bidi
        reordering on its own, so Persian subject names render with
        disconnected/reversed letters. Reshape + reorder here so they
        display correctly in the chart legend.
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
CHART_SUBTEXT = "#8b949e"
SLICE_COLORS = [
    "#39d353", "#58a6ff", "#f0ad4e", "#e05780", "#a78bfa",
    "#2dd4bf", "#f97316", "#facc15", "#60a5fa", "#f472b6",
    "#4ade80", "#c084fc",
]

MIN_LABELED_PERCENT = 4.0

# Legend wraps into a second column once there are more subjects than this.
LEGEND_WRAP_THRESHOLD = 8


class ReportFrame(tb.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, padding=15)

        self.db = db

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.build_ui()

    # UI construction
    def build_ui(self):
        self._build_title()
        self._build_date_range_card()
        self._build_chart_card()
        self._build_results_card()
        self._build_statistics_card()

        self.show_range_summary()

    def _build_title(self):
        title = tb.Label(
            self,
            text="Study Report",
            font=("Segoe UI", 18, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

    def _build_date_range_card(self):
        controls = tb.Labelframe(
            self,
            text="Date Range",
            padding=15,
            bootstyle="primary"
        )
        controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        controls.columnconfigure(6, weight=1)

        tb.Label(controls, text="From").grid(row=0, column=0, padx=(0, 5))
        self.start_date_entry = self._make_date_widget(controls)
        self.start_date_entry.grid(row=0, column=1, padx=(0, 20))

        tb.Label(controls, text="To").grid(row=0, column=2, padx=(0, 5))
        self.end_date_entry = self._make_date_widget(controls)
        self.end_date_entry.grid(row=0, column=3, padx=(0, 30))

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
        ).grid(row=0, column=5, padx=5)

        tb.Button(
            controls,
            text="Total Study",
            command=self.show_total_study,
            bootstyle="info"
        ).grid(row=0, column=6, sticky="w", padx=5)

    def _make_date_widget(self, parent):
        if HAS_DATEENTRY:
            widget = DateEntry(parent, dateformat="%Y-%m-%d", width=12, bootstyle="primary")
        else:
            widget = tb.Entry(parent, width=14, justify="center")
            widget.insert(0, today_str())
        return widget

    def _build_chart_card(self):
        chart_frame = tb.Labelframe(
            self,
            text="Study Distribution",
            padding=10,
            bootstyle="primary"
        )
        chart_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(4.6, 4.2), dpi=100, facecolor=CHART_BG)
        self.ax = self.figure.add_subplot(111)

        self.chart_canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        chart_widget = self.chart_canvas.get_tk_widget()
        chart_widget.grid(row=0, column=0, sticky="nsew")

        chart_widget.bind("<Configure>", self._on_chart_resize)

    def _build_results_card(self):
        result_frame = tb.Labelframe(
            self,
            text="Results",
            padding=10,
            bootstyle="primary"
        )
        result_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.tree = tb.Treeview(
            result_frame,
            columns=("subject", "time", "percentage"),
            show="headings",
            bootstyle="primary"
        )

        self.tree.heading("subject", text="Subject")
        self.tree.heading("time", text="Study Time")
        self.tree.heading("percentage", text="Percentage")

        self.tree.column("subject", anchor="center", width=200)
        self.tree.column("time", anchor="center", width=160)
        self.tree.column("percentage", anchor="center", width=100)

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = tb.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="round"
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _build_statistics_card(self):
        stats_card = tb.Labelframe(
            self,
            text="Statistics",
            padding=12,
            bootstyle="primary"
        )
        stats_card.grid(row=3, column=0, sticky="ew", pady=(15, 0), padx=(0, 8))
        stats_card.columnconfigure((0, 1), weight=1)

        self.total_label = self._make_stat_label(stats_card, row=0, column=0)
        self.average_label = self._make_stat_label(stats_card, row=0, column=1)
        self.most_label = self._make_stat_label(stats_card, row=1, column=0)
        self.least_label = self._make_stat_label(stats_card, row=1, column=1)

    def _make_stat_label(self, parent, row, column):
        label = tb.Label(
            parent,
            text="",
            font=("Segoe UI", 10, "bold"),
            bootstyle="success"
        )
        label.grid(row=row, column=column, sticky="w", pady=3, padx=5)
        return label

    # Resize handling
    def _on_chart_resize(self, event):
        if event.width < 50 or event.height < 50:
            return
        dpi = self.figure.get_dpi()
        self.figure.set_size_inches(event.width / dpi, event.height / dpi)
        self.chart_canvas.draw_idle()

    def _read_date(self, widget):
        """Return the YYYY-MM-DD text from either a DateEntry or an Entry."""
        if hasattr(widget, "entry"):
            return widget.entry.get().strip()
        return widget.get().strip()

    def _get_validated_range(self):
        start = self._read_date(self.start_date_entry)
        end = self._read_date(self.end_date_entry)

        if not is_valid_date(start) or not is_valid_date(end):
            messagebox.showerror("Error", "Date format must be YYYY-MM-DD.")
            return None

        if start > end:
            messagebox.showerror("Error", "Start date must be before end date.")
            return None

        return start, end

    def show_range_summary(self):
        date_range = self._get_validated_range()
        if date_range is None:
            return

        start, end = date_range
        summary = self.db.get_subject_percentages(start, end)
        self._apply_summary(summary)

    def show_day_detail(self):
        date = self._read_date(self.start_date_entry)

        if not is_valid_date(date):
            messagebox.showerror("Error", "Date format must be YYYY-MM-DD.")
            return

        summary = self.db.get_subject_percentages(date, date)
        self._apply_summary(summary)

    def show_total_study(self):
        summary = self.db.get_subject_percentages()
        self._apply_summary(summary)

    # Rendering (table + donut + statistics all share one summary)
    def _apply_summary(self, summary):
        self._render_table(summary)
        self._draw_donut(summary)
        self._update_statistics(summary)

    def _render_table(self, summary):
        for row in self.tree.get_children():
            self.tree.delete(row)

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

    def _update_statistics(self, summary):
        if not summary:
            for label in (self.total_label, self.average_label, self.most_label, self.least_label):
                label.config(text="No data")
            return

        total = sum(item["total_minutes"] for item in summary)
        average = total / len(summary)
        most_studied = summary[0]
        least_studied = summary[-1]

        self.total_label.config(text=f"Total: {minutes_to_hm_text(total)}")
        self.average_label.config(text=f"Average: {minutes_to_hm_text(round(average))}")
        self.most_label.config(
            text=f"Most Studied: {most_studied['subject_name']} ({minutes_to_hm_text(most_studied['total_minutes'])})"
        )
        self.least_label.config(
            text=f"Least Studied: {least_studied['subject_name']} ({minutes_to_hm_text(least_studied['total_minutes'])})"
        )

    def _draw_donut(self, summary):
        total_minutes = sum(item["total_minutes"] for item in summary)

        self.ax.clear()
        self.figure.set_facecolor(CHART_BG)
        self.ax.set_facecolor(CHART_BG)

        if not summary or total_minutes <= 0:
            self._draw_empty_chart()
            return

        labels = [_fix_rtl(item["subject_name"]) for item in summary]
        sizes = [item["total_minutes"] for item in summary]
        colors = [SLICE_COLORS[i % len(SLICE_COLORS)] for i in range(len(summary))]

        def autopct(pct):
            return f"{pct:.1f}%" if pct >= MIN_LABELED_PERCENT else ""

        wedges, _texts, _autotexts = self.ax.pie(
            sizes,
            colors=colors,
            autopct=autopct,
            pctdistance=0.82,
            startangle=90,
            wedgeprops={"width": 0.42, "edgecolor": CHART_BG, "linewidth": 2},
            textprops={"color": CHART_BG, "fontsize": 8, "weight": "bold"},
        )

        self._draw_center_text(total_minutes)
        self._draw_legend(wedges, labels)

        self.ax.axis("equal")
        # Leave room on the right for the legend; the fractions below are relative, so they hold up when the figure is resized.
        legend_cols = 2 if len(summary) > LEGEND_WRAP_THRESHOLD else 1
        right_margin = 0.55 if legend_cols == 2 else 0.68
        self.figure.subplots_adjust(left=0.02, right=right_margin, top=0.95, bottom=0.05)

        self.chart_canvas.draw_idle()

    def _draw_empty_chart(self):
        self.ax.text(
            0.5, 0.5, "No study data for selected period",
            ha="center", va="center", color=CHART_TEXT, fontsize=11,
            transform=self.ax.transAxes, wrap=True
        )
        self.ax.axis("off")
        self.chart_canvas.draw_idle()

    def _draw_center_text(self, total_minutes):
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
            ha="center", va="center", color=CHART_SUBTEXT, fontsize=9
        )

    def _draw_legend(self, wedges, labels):
        legend_cols = 2 if len(labels) > LEGEND_WRAP_THRESHOLD else 1
        self.ax.legend(
            wedges, labels,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            ncol=legend_cols,
            frameon=False,
            fontsize=8,
            labelcolor=CHART_TEXT,
        )