"""Daily study reminder (Android only).

Flet has no built-in notifications, so this uses the community package
`flet-android-notifications`. If the package is not installed (for example
while testing on your computer) every call just returns "unavailable" and the
rest of the app keeps working.

The reminder is handed to Android's AlarmManager, so it fires even when the
app is closed. Python does not need to be running.
"""

from __future__ import annotations

from datetime import datetime, timedelta

try:
    from flet_android_notifications import FletAndroidNotifications
except Exception:  # package missing or not usable on this platform
    FletAndroidNotifications = None  # type: ignore[assignment,misc]

REMINDER_ID = 1001  # fixed id, so scheduling again replaces the old reminder


class Reminders:
    def __init__(self) -> None:
        self._service = None
        if FletAndroidNotifications is not None:
            try:
                # Keep a reference: Flet drops services without live references.
                self._service = FletAndroidNotifications()
            except Exception as exc:
                print("Notifications unavailable:", exc)

    async def _exact_allowed(self, ask: bool) -> bool:
        """Can we use exact alarms? (Android 12+ needs 'Alarms & reminders'.)"""
        service = self._service
        try:
            if await service.can_schedule_exact_notifications():
                return True
            if ask:
                # Opens the system screen where the user can allow it.
                return bool(await service.request_exact_alarm_permission())
        except Exception as exc:
            print("Exact alarm check failed:", exc)
        return False

    async def apply(
        self,
        enabled: bool,
        hour: int,
        minute: int,
        title: str,
        body: str,
        interactive: bool = False,
    ) -> str:
        """Returns: unavailable | cancelled | denied | scheduled |
        scheduled_inexact | error.

        interactive=True (the user pressed Save) may show permission prompts.
        interactive=False (app start) never opens any screen.
        """
        service = self._service
        if service is None:
            return "unavailable"
        try:
            await service.cancel(REMINDER_ID)  # remove the old reminder first
            if not enabled:
                return "cancelled"

            if interactive:
                granted = await service.request_permissions()
                if granted is False:
                    return "denied"
            exact = await self._exact_allowed(interactive)

            # An aware datetime keeps the exact instant; the plugin then repeats
            # it every day at the same time of day.
            now = datetime.now().astimezone()
            first = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if first <= now:
                first += timedelta(days=1)
            await service.schedule_notification(
                notification_id=REMINDER_ID,
                title=title,
                body=body,
                scheduled_time=first,
                schedule_mode="exact_allow_while_idle" if exact else "inexact_allow_while_idle",
                match_date_time_components="time",  # repeat every day at this time
            )
            return "scheduled" if exact else "scheduled_inexact"
        except Exception as exc:
            print("Reminder error:", exc)
            return "error"

    async def test(self, title: str, body: str) -> str:
        """Show a notification right now. Returns: unavailable | denied | sent | error."""
        service = self._service
        if service is None:
            return "unavailable"
        try:
            granted = await service.request_permissions()
            if granted is False:
                return "denied"
            await service.show_notification(
                notification_id=REMINDER_ID + 1, title=title, body=body
            )
            return "sent"
        except Exception as exc:
            print("Test notification error:", exc)
            return "error"
