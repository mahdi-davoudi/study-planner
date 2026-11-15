# Study Planner

Track your daily study time per subject, see your progress on an activity
heatmap, and review reports. Available as a **Windows desktop app** and an
**Android app**.

Supports **English** and **Persian (فارسی)** with right-to-left layout, and
dark / light themes.

<!-- Add screenshots here, e.g.
![Windows](docs/windows.png) ![Android](docs/android.png)
-->

## Features

| Feature | Windows | Android |
|---|:---:|:---:|
| Log study time per subject and per day (hours + minutes) | ✅ | ✅ |
| Repeated logs for the same subject on the same day are added together | ✅ | ✅ |
| Study timer (start / pause / stop), rounded to 5 minutes | ✅ | ✅ |
| Activity heatmap and streak | ✅ | ✅ |
| Reports by period (per-subject share) | ✅ | ✅ |
| Edit / delete saved records | ✅ | ✅ |
| English / Persian, dark / light theme | ✅ | ✅ |
| Daily study reminder notification | — | ✅ |

> The two versions are separate apps with their own data. There is no sync or
> import between them yet.

## Repository layout

```
study-planner/
├── windows/    Desktop app (Python + PySide6)
├── mobile/     Android app (Python + Flet)
└── .github/
    └── workflows/
        └── build-mobile-apk.yml    Builds the Android APK on GitHub
```

## Windows

See [`windows/README.md`](windows/README.md) for how to run it from source or
build a standalone `.exe`.

## Android

The mobile app is written with [Flet](https://flet.dev) and built into an APK.

### Get the APK (no setup on your computer)

1. Open the **Actions** tab of this repository.
2. Choose **Build Android APK** → **Run workflow**.
3. When it finishes (about 15–30 minutes), open the run and download the
   **study-planner-apk** artifact (a zip containing the `.apk`).
4. Copy the APK to your phone and install it. Android will ask you to allow
   installing from this source.

### Run on your computer (for development)

```bash
cd mobile
python -m venv venv
venv\Scripts\activate        # Windows (use `source venv/bin/activate` on Linux/macOS)
pip install "flet[all]"
flet run
```

To preview a phone-sized layout in the browser: `flet run --web`, then use the
device toolbar of your browser's developer tools.

### Build the APK locally

```bash
cd mobile
flet build apk -v
```

The first build downloads Flutter, a JDK and the Android SDK, so it takes a
while and needs access to Google and pub.dev servers. If those are blocked in
your region, use the GitHub Actions workflow above instead.

### Daily reminder

The reminder uses the community package
[`flet-android-notifications`](https://pypi.org/project/flet-android-notifications/).
It needs the notification permission, and the "Alarms & reminders" permission
for exact timing on Android 12+. The settings page has a **Send a test
notification** button to check that notifications work on your phone. Some
phone brands also require excluding the app from battery optimization.

### Where the data is stored

The database (`study_planner.db`) lives in the app's private storage. It is
deleted when you uninstall the app or clear its data. Installing a new APK
over an old one keeps the data, but only if both APKs are signed with the same
key (APKs built by the default workflow may not be). Export / import is not
available yet.

## Known limitations

- iOS is not supported.
- No cloud sync and no data import/export between devices.
- The reminder depends on the phone's battery management.

## License

Add a license file (for example MIT) and mention it here.
