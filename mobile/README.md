# Study Planner – Android (Flet)

Android version of Study Planner, written in Python with
[Flet](https://flet.dev) (Flutter under the hood) and packaged as an APK.

## Features

- Log study time per subject and per day with **hours + minutes** inputs
  (minutes are limited to 0–59, hours to 12). Repeated logs for the same
  subject on the same day are added together.
- **Study timer** (start / pause / resume / stop & save). The result is rounded
  to the nearest 5 minutes; sessions under 2.5 minutes are not saved.
  The timer survives the app going to the background or being closed.
- Activity heatmap (last 18 weeks), current streak, weekly and monthly totals.
- Reports for today / 7 days / 30 days / this month / this year / all time.
- Edit or delete the records of any day (from the home page).
- **Daily reminder notification** with a 12-hour time picker (AM / PM).
- English and Persian (right-to-left), dark and light themes.
- Optional background images (`bg_dark.jpg`, `bg_light.jpg`) and
  semi-transparent cards.

### Differences from the Windows version

- The "Edit logs" page is merged into the home page (edit / delete icons under
  the selected day).
- The heatmap shows the last 18 weeks so it fits a phone screen.
- The report uses a stacked bar and a legend instead of a donut chart.
- No custom date range in reports yet (preset periods only).

## Project structure

```
mobile/
├── pyproject.toml            Flet / build configuration and dependencies
└── src/
    ├── main.py               App shell: navigation, theme, language, timer loop
    ├── config.py             Database path (app storage folder)
    ├── database.py           SQLite storage layer (+ settings table)
    ├── i18n.py               English / Persian strings
    ├── palette.py            Dark / light colours
    ├── ui.py                 Shared widgets (cards, buttons, dialogs, inputs)
    ├── timer_state.py        Stopwatch state, saved in the database
    ├── reminders.py          Daily reminder (Android notifications)
    ├── pages/                add_page, timer_page, report_page,
    │                         subjects_page, settings_page
    ├── utils/helpers.py      Time formatting helpers
    └── assets/               icon.png, bg_dark.jpg, bg_light.jpg
```

## Run on your computer

```bash
cd mobile
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install "flet[all]"
flet run
```

Keep the `venv` folder **outside** `src/`, because everything inside `src/` is
packaged into the APK.

To preview a phone-sized layout, run `flet run --web` and use your browser's
device toolbar (F12 → Toggle device toolbar).

Notifications do not work on the desktop: the reminder settings will say that
reminders only work in the Android app. This is expected.

## Build the APK

### On GitHub (recommended)

The repository has a workflow that builds the APK on GitHub's servers, so you
do not have to install Flutter or the Android SDK:

1. Open the **Actions** tab → **Build Android APK** → **Run workflow**.
2. Wait about 15–30 minutes.
3. Open the finished run and download the **study-planner-apk** artifact.

### On your own computer

```bash
cd mobile
flet build apk -v
```

The first build downloads Flutter, a JDK and the Android SDK and needs access
to Google and pub.dev servers. If they are blocked in your region, use the
GitHub workflow.

### Notification package

The reminder uses
[`flet-android-notifications`](https://pypi.org/project/flet-android-notifications/).
It needs a small patch of the generated Android project, so the workflow runs:

1. `flet build apk` (generates `build/flutter`; this first build may fail at the
   Gradle step, which is expected),
2. `flet-android-notifications-patch --project-root build/flutter`,
3. `flet build apk` again.

`pyproject.toml` also declares the exact-alarm permission:

```toml
[tool.flet.android.permission]
"android.permission.SCHEDULE_EXACT_ALARM" = true
```

## Install on a phone

Copy the APK to the phone, open it, and allow installing from that source
(Android asks the first time). If Play Protect warns about the app, choose
**Install anyway**: the APK is not signed for the Play Store.

## Daily reminder

Settings → Daily reminder → turn it on, choose hour, minute and AM / PM, and
press **Save**.

- On Android 12+, allow **Alarms & reminders** for the app when asked, then
  press Save again. Without it the reminder still works but Android may show it
  a few minutes late (the app tells you which case you are in).
- Use **Send a test notification** to check that notifications work at all.
- Some phone brands stop background apps aggressively. If the reminder does not
  show, exclude the app from battery optimization in the phone settings.

## Data

- The database (`study_planner.db`) is stored in the app's private storage
  (the folder given by Flet's `FLET_APP_STORAGE_DATA`). Other apps and the file
  manager cannot see it.
- It is deleted when you uninstall the app or clear its data.
- Android only installs an update over an existing app if both APKs are signed
  with the same key. APKs from the default workflow may use a different key
  each time; in that case you must uninstall first, which deletes the data.
  A fixed signing key and export / import of the database are planned.
- The Windows and Android versions have separate databases (no sync).

## Troubleshooting

- **`TOMLDecodeError: Cannot overwrite a value`** when building: a key is
  defined twice in `pyproject.toml` (for example two `dependencies` lines or
  two `[tool.flet.android.permission]` sections). Keep only one of each.
- **`AndroidManifest.xml not found` in the patch step**: the first build
  stopped before creating `build/flutter`. Open the log of the first build step
  to see the real error.
- **The APK is huge or the build is very slow**: make sure `venv`, `.flet` and
  `build` folders are not inside `src/`.
- **Text with mixed English and Persian looks reordered**: subject names are
  wrapped in Unicode direction isolates inside sentences. If you still see a
  place where it breaks, report it with a screenshot.
- **Reminder does not appear**: see "Daily reminder" above.

## Known limitations

- Android only (no iOS build).
- No cloud sync, no export / import yet.
- The background images, if you use Telegram's chat wallpaper, may have
  licensing restrictions for public distribution. Prefer your own or a freely
  licensed pattern.
