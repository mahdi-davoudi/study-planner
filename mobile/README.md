# Study Planner (Flet / mobile)

## Run on your computer (fast test)
    pip install "flet[all]"
    flet run

## Build the Android APK
    flet build apk -v
    # result: build/apk/*.apk

## Daily reminder (Android only) - phase 2
In pyproject.toml set:

    dependencies = ["flet", "flet-android-notifications"]

    [tool.flet.android.permission]
    "android.permission.POST_NOTIFICATIONS" = true
    "android.permission.RECEIVE_BOOT_COMPLETED" = true

Then: flet build apk -v   (first run may stop at the Gradle step),
      flet-android-notifications-patch --project-root build/flutter
      flet build apk -v
