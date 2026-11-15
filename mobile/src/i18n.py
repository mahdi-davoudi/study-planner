from __future__ import annotations

from datetime import date

LANGUAGES: dict[str, str] = {"en": "English", "fa": "فارسی"}
RTL_LANGUAGES: frozenset[str] = frozenset({"fa"})
DEFAULT_LANGUAGE = "en"

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# Translations. Keys missing from a language fall back to English.
STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # app / navigation
        "app.name": "Study Planner",
        "app.tagline": "Track · Review · Improve",
        "nav.add": "Add Study",
        "nav.subjects": "Subjects",
        "nav.reports": "Reports",
        "nav.edit": "Edit Logs",
        "nav.timer": "Study Timer",
        "nav.settings": "Settings",
        "lang.switch_to": "Switch to {name}",
        "lang.short": "FA",
        "theme.to_light": "Switch to light theme",
        "theme.to_dark": "Switch to dark theme",
        # common
        "common.date": "Date",
        "common.total": "Total",
        "common.today": "Today",
        "common.from": "From",
        "common.to": "To",
        "common.error": "Error",
        "common.notice": "Notice",
        "common.confirm_delete": "Confirm Delete",
        "common.yes": "Yes",
        "common.no": "No",
        "common.cancel": "Cancel",
        "common.save": "Save",
        # stat cards
        "stat.streak": "Streak",
        "stat.week": "This week",
        "stat.month": "This month",
        "streak.one": "{n} day",
        "streak.other": "{n} days",
        # add page
        "add.title": "Add Study Log",
        "add.activity": "Study Activity",
        "add.activity_year": "Study Activity ({year})",
        "add.details": "Day details",
        "add.details_hint": "Click a day on the heatmap to load its date and see what was studied.",
        "add.day_title": "Day details - {iso}",
        "add.no_records": "No study records for this day.",
        "add.log_card": "Log study time",
        "add.save": "Save Study Log",
        "add.no_subjects": "No subjects yet. Add some from the Subjects page first.",
        "add.min_suffix": " min",
        "add.hours_label": "Hours",
        "add.minutes_label": "Minutes",
        "add.need_minutes": "Enter study time for at least one subject.",
        "add.saved.one": "Saved {n} subject for {iso} (total {total}).",
        "add.saved.other": "Saved {n} subjects for {iso} (total {total}).",
        # subjects page
        "sub.title": "Manage Subjects",
        "sub.add_card": "Add a subject",
        "sub.placeholder": "Subject name",
        "sub.add_btn": "Add Subject",
        "sub.list_card": "Subject list",
        "sub.col_name": "Subject name",
        "sub.col_added": "Added",
        "sub.rename": "Rename",
        "sub.delete": "Delete Selected Subject",
        "sub.enter_name": "Enter a subject name.",
        "sub.exists": "This subject already exists.",
        "sub.rename_title": "Rename Subject",
        "sub.new_name": "New name:",
        "sub.exists_other": "A subject with this name already exists.",
        "sub.delete_q": (
            "Delete subject '{name}'?\n"
            "(Previously logged study records for this subject will remain in reports.)"
        ),
        # report page
        "rep.title": "Study Report",
        "rep.range_card": "Date range",
        "rep.showing_all": "Showing: all time",
        "rep.showing": "Showing: {start} → {end}",
        "rep.distribution": "Study distribution",
        "rep.results": "Results",
        "rep.col_subject": "Subject",
        "rep.col_time": "Study time",
        "rep.col_share": "Share",
        "rep.average": "Average per subject",
        "rep.most": "Most studied",
        "rep.least": "Least studied",
        "rep.no_data": "No data",
        "preset.7": "7 days",
        "preset.30": "30 days",
        "preset.year": "This year",
        "preset.all": "All time",
        # edit page
        "edit.title": "Edit / Delete Saved Records",
        "edit.day_card": "Day",
        "edit.records_card": "Records for selected day",
        "edit.empty": "No records for this day.",
        "edit.tip": "Tip: double-click a row to edit it.",
        "edit.edit_btn": "Edit Time",
        "edit.delete_btn": "Delete Selected Record",
        "edit.delete_q": "Delete the record '{name} - {time}'?",
        "edit.dialog_title": "Edit Study Time",
        "edit.minutes_prompt": "{name} (minutes):",
        # heatmap / donut
        "heat.less": "Less",
        "heat.more": "More",
        "heat.tooltip": "Study time: {time}",
        "wd.mon": "Mon",
        "wd.wed": "Wed",
        "wd.fri": "Fri",
        "donut.empty": "No study data for\nthe selected period",
        # durations
        "time.both": "{h} hours and {m} minutes",
        "time.hours": "{h} hours",
        "time.minutes": "{m} minutes",
        # timer page
        "timer.title": "Study Timer",
        "timer.card": "Stopwatch",
        "timer.subject": "Subject",
        "timer.start": "Start",
        "timer.pause": "Pause",
        "timer.resume": "Resume",
        "timer.stop": "Stop & Save",
        "timer.discard": "Discard",
        "timer.idle": "Choose a subject and press Start.",
        "timer.running": "Studying: {name}",
        "timer.paused": "Paused: {name}",
        "timer.preview": "Will be logged as: {time}",
        "timer.too_short": "The session was under 2.5 minutes, so nothing was saved.",
        "timer.saved": "Saved {time} for {name}. Today's total for it: {total}.",
        "timer.discard_q": "Discard this session without saving?",
        "timer.quit_q": "A study session is still in progress. Quit without saving it?",
        # settings page (new)
        "settings.title": "Settings",
        "settings.language": "Language",
        "settings.theme": "Theme",
        "settings.dark": "Dark",
        "settings.light": "Light",
        "settings.reminder": "Daily reminder",
        "settings.reminder_on": "Remind me to study every day",
        "settings.reminder_time": "Reminder time",
        "settings.hour": "Hour",
        "settings.minute": "Minute",
        "settings.am": "AM",
        "settings.pm": "PM",
        "settings.reminder_inexact": "Reminder set for {time}, but Android may show it a few minutes late. Allow \"Alarms & reminders\" for this app (phone settings) to make it exact, then press Save again.",
        "settings.reminder_save": "Save reminder",
        "settings.bad_time": "Enter an hour from 1 to 12 and minutes from 0 to 59.",
        "settings.reminder_scheduled": "Reminder set for {time} every day.",
        "settings.reminder_cancelled": "Reminder turned off.",
        "settings.reminder_denied": "Notification permission was denied. Enable it in the phone settings.",
        "settings.reminder_unavailable": "Reminders work only in the Android app.",
        "settings.reminder_error": "Could not schedule the reminder.",
        "settings.reminder_test": "Send a test notification",
        "settings.test_sent": "Test notification sent.",
        "reminder.title": "Time to study 📚",
        "reminder.body": "Open Study Planner and start your timer.",
    },
    "fa": {
        "app.name": "برنامه‌ریز مطالعه",
        "app.tagline": "ثبت · مرور · پیشرفت",
        "nav.add": "ثبت مطالعه",
        "nav.subjects": "درس‌ها",
        "nav.reports": "گزارش‌ها",
        "nav.edit": "ویرایش سوابق",
        "nav.timer": "تایمر مطالعه",
        "nav.settings": "تنظیمات",
        "lang.switch_to": "تغییر به {name}",
        "lang.short": "EN",
        "theme.to_light": "تغییر به تم روشن",
        "theme.to_dark": "تغییر به تم تاریک",
        "common.date": "تاریخ",
        "common.total": "مجموع",
        "common.today": "امروز",
        "common.from": "از",
        "common.to": "تا",
        "common.error": "خطا",
        "common.notice": "توجه",
        "common.confirm_delete": "تأیید حذف",
        "common.yes": "بله",
        "common.no": "خیر",
        "common.cancel": "انصراف",
        "common.save": "ذخیره",
        "stat.streak": "روزهای متوالی",
        "stat.week": "این هفته",
        "stat.month": "این ماه",
        "streak.one": "{n} روز",
        "streak.other": "{n} روز",
        "add.title": "ثبت مطالعه",
        "add.activity": "فعالیت مطالعه",
        "add.activity_year": "فعالیت مطالعه ({year})",
        "add.details": "جزئیات روز",
        "add.details_hint": (
            "روی یک روز در نقشهٔ فعالیت کلیک کنید تا تاریخ آن بارگذاری شود "
            "و مطالعه‌های همان روز را ببینید."
        ),
        "add.day_title": "جزئیات روز - {iso}",
        "add.no_records": "برای این روز مطالعه‌ای ثبت نشده است.",
        "add.log_card": "ثبت زمان مطالعه",
        "add.save": "ذخیرهٔ مطالعه",
        "add.no_subjects": "هنوز درسی ثبت نشده است. ابتدا از صفحهٔ «درس‌ها» چند درس اضافه کنید.",
        "add.min_suffix": " دقیقه",
        "add.hours_label": "ساعت",
        "add.minutes_label": "دقیقه",
        "add.need_minutes": "برای دست‌کم یک درس زمان وارد کنید.",
        "add.saved.one": "{n} درس برای {iso} ذخیره شد (مجموع {total}).",
        "add.saved.other": "{n} درس برای {iso} ذخیره شد (مجموع {total}).",
        "sub.title": "مدیریت درس‌ها",
        "sub.add_card": "افزودن درس",
        "sub.placeholder": "نام درس",
        "sub.add_btn": "افزودن درس",
        "sub.list_card": "فهرست درس‌ها",
        "sub.col_name": "نام درس",
        "sub.col_added": "تاریخ افزودن",
        "sub.rename": "تغییر نام",
        "sub.delete": "حذف درس انتخاب‌شده",
        "sub.enter_name": "نام درس را وارد کنید.",
        "sub.exists": "این درس از قبل وجود دارد.",
        "sub.rename_title": "تغییر نام درس",
        "sub.new_name": "نام جدید:",
        "sub.exists_other": "درسی با این نام از قبل وجود دارد.",
        "sub.delete_q": (
            "درس «{name}» حذف شود؟\n"
            "(سوابق مطالعهٔ قبلی این درس در گزارش‌ها باقی می‌مانند.)"
        ),
        "rep.title": "گزارش مطالعه",
        "rep.range_card": "بازهٔ زمانی",
        "rep.showing_all": "نمایش: همهٔ زمان‌ها",
        "rep.showing": "نمایش: از {start} تا {end}",
        "rep.distribution": "توزیع مطالعه",
        "rep.results": "نتایج",
        "rep.col_subject": "درس",
        "rep.col_time": "زمان مطالعه",
        "rep.col_share": "سهم",
        "rep.average": "میانگین هر درس",
        "rep.most": "بیشترین مطالعه",
        "rep.least": "کمترین مطالعه",
        "rep.no_data": "بدون داده",
        "preset.7": "7 روز",
        "preset.30": "30 روز",
        "preset.year": "امسال",
        "preset.all": "همهٔ زمان‌ها",
        "edit.title": "ویرایش / حذف سوابق ذخیره‌شده",
        "edit.day_card": "روز",
        "edit.records_card": "سوابق روز انتخاب‌شده",
        "edit.empty": "برای این روز سابقه‌ای وجود ندارد.",
        "edit.tip": "نکته: برای ویرایش، روی یک ردیف دوبار کلیک کنید.",
        "edit.edit_btn": "ویرایش زمان",
        "edit.delete_btn": "حذف سابقهٔ انتخاب‌شده",
        "edit.delete_q": "سابقهٔ «{name} - {time}» حذف شود؟",
        "edit.dialog_title": "ویرایش زمان مطالعه",
        "edit.minutes_prompt": "{name} (دقیقه):",
        "heat.less": "کم",
        "heat.more": "زیاد",
        "heat.tooltip": "زمان مطالعه: {time}",
        "wd.mon": "د",
        "wd.wed": "چ",
        "wd.fri": "ج",
        "donut.empty": "برای بازهٔ انتخاب‌شده\nداده‌ای وجود ندارد",
        "time.both": "{h} ساعت و {m} دقیقه",
        "time.hours": "{h} ساعت",
        "time.minutes": "{m} دقیقه",
        "timer.title": "تایمر مطالعه",
        "timer.card": "کرنومتر",
        "timer.subject": "درس",
        "timer.start": "شروع",
        "timer.pause": "توقف موقت",
        "timer.resume": "ادامه",
        "timer.stop": "پایان و ذخیره",
        "timer.discard": "لغو",
        "timer.idle": "یک درس انتخاب کنید و «شروع» را بزنید.",
        "timer.running": "در حال مطالعه: {name}",
        "timer.paused": "متوقف شد: {name}",
        "timer.preview": "ثبت خواهد شد: {time}",
        "timer.too_short": "جلسه کمتر از ۲٫۵ دقیقه بود و چیزی ذخیره نشد.",
        "timer.saved": "{time} برای «{name}» ذخیره شد. مجموع امروز این درس: {total}.",
        "timer.discard_q": "این جلسه بدون ذخیره حذف شود؟",
        "timer.quit_q": "یک جلسهٔ مطالعه هنوز در جریان است. بدون ذخیره خارج می‌شوید؟",
        "settings.title": "تنظیمات",
        "settings.language": "زبان",
        "settings.theme": "تم",
        "settings.dark": "تاریک",
        "settings.light": "روشن",
        "settings.reminder": "یادآور روزانه",
        "settings.reminder_on": "هر روز برای مطالعه یادآوری کن",
        "settings.reminder_time": "زمان یادآور",
        "settings.hour": "ساعت",
        "settings.minute": "دقیقه",
        "settings.am": "ق.ظ",
        "settings.pm": "ب.ظ",
        "settings.reminder_inexact": "یادآور برای {time} تنظیم شد، ولی ممکن است اندروید آن را چند دقیقه دیرتر نشان بدهد. برای دقیق شدن، در تنظیمات گوشی مجوز «آلارم‌ها و یادآورها» را برای این برنامه فعال کنید و دوباره «ذخیره» را بزنید.",
        "settings.reminder_save": "ذخیرهٔ یادآور",
        "settings.bad_time": "ساعت را از 1 تا 12 و دقیقه را از 0 تا 59 وارد کنید.",
        "settings.reminder_scheduled": "یادآور هر روز ساعت {time} تنظیم شد.",
        "settings.reminder_cancelled": "یادآور خاموش شد.",
        "settings.reminder_denied": "اجازهٔ نوتیفیکیشن داده نشد. آن را از تنظیمات گوشی فعال کنید.",
        "settings.reminder_unavailable": "یادآور فقط در برنامهٔ اندروید کار می‌کند.",
        "settings.reminder_error": "تنظیم یادآور انجام نشد.",
        "settings.reminder_test": "ارسال نوتیفیکیشن آزمایشی",
        "settings.test_sent": "نوتیفیکیشن آزمایشی ارسال شد.",
        "reminder.title": "وقت مطالعه است 📚",
        "reminder.body": "برنامهٔ مطالعه را باز کنید و تایمر را شروع کنید.",
    },
}

# Weekday index follows ``date.weekday()`` (Monday == 0).
WEEKDAYS: dict[str, list[str]] = {
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "fa": ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"],
}
MONTHS: dict[str, list[str]] = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fa": ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
           "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"],
}


class LanguageManager:
    """Holds the current language. Persisting it is done by main.py."""

    def __init__(self) -> None:
        self._language = DEFAULT_LANGUAGE

    @property
    def language(self) -> str:
        return self._language

    @property
    def is_rtl(self) -> bool:
        return self._language in RTL_LANGUAGES

    @property
    def other_language(self) -> str:
        return "en" if self._language == "fa" else "fa"

    def set_language(self, language: str) -> None:
        if language in LANGUAGES:
            self._language = language

    def toggle(self) -> None:
        self.set_language(self.other_language)


manager = LanguageManager()


def localize_digits(text: str) -> str:
    return text.translate(_PERSIAN_DIGITS) if manager.language == "fa" else text


_FSI = "\u2068"  # first-strong isolate
_PDI = "\u2069"  # pop directional isolate


def isolate(text: str) -> str:
    """Keep `text` (a subject name, a date...) from reordering the sentence
    around it when its direction differs from the sentence's direction."""
    return f"{_FSI}{text}{_PDI}"


def tr(key: str, **kwargs: object) -> str:
    text = STRINGS[manager.language].get(key) or STRINGS["en"].get(key) or key
    if kwargs:
        safe = {k: isolate(v) if isinstance(v, str) else v for k, v in kwargs.items()}
        text = text.format(**safe)
    return localize_digits(text)


def tr_n(key: str, n: int, **kwargs: object) -> str:
    suffix = "one" if n == 1 else "other"
    return tr(f"{key}.{suffix}", n=n, **kwargs)


def month_name(month: int) -> str:
    return MONTHS[manager.language][month - 1]


def format_date(day: date) -> str:
    weekday = WEEKDAYS[manager.language][day.weekday()]
    if manager.language == "en":
        return f"{weekday}, {day.day:02d} {month_name(day.month)} {day.year}"
    return localize_digits(f"{weekday} {day.day} {month_name(day.month)} {day.year}")
