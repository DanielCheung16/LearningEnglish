import json
import logging
import os
from datetime import datetime
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .email_manager import EmailManager
from .review_manager import ReviewManager


class ReviewScheduler:
    """Manage background jobs for review reminders."""

    def __init__(self, data_dir: str = "backend/data"):
        self.scheduler = BackgroundScheduler()
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "user_config.json")
        self.is_running = False

        logging.basicConfig()
        logging.getLogger("apscheduler").setLevel(logging.WARNING)

    def _read_config(self) -> dict:
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_config(self, config: dict):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _get_email_settings(self, config: dict) -> dict:
        email_settings = config.setdefault("email_settings", {})
        email_settings.setdefault("enable_reminders", False)
        email_settings.setdefault("reminder_time", "09:00")
        email_settings.setdefault("smtp_server", "smtp.gmail.com")
        email_settings.setdefault("smtp_port", 587)
        email_settings.setdefault("sender_email", "")
        email_settings.setdefault("app_password", "")
        email_settings.setdefault("last_sent_date", "")
        return email_settings

    def _mark_reminder_sent(self, config: dict, sent_date: str):
        email_settings = self._get_email_settings(config)
        email_settings["last_sent_date"] = sent_date
        self._write_config(config)

    def _parse_reminder_time(self, reminder_time: str) -> tuple[int, int]:
        try:
            hour, minute = map(int, reminder_time.split(":"))
            return hour, minute
        except (ValueError, AttributeError):
            return 9, 0

    def start(self):
        if self.is_running:
            print("Scheduler is already running.")
            return

        self.scheduler.start()
        self.is_running = True
        print("Scheduler started.")

        self._schedule_daily_reminder()
        self._send_missed_reminder_if_needed()

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("Scheduler stopped.")

    def _schedule_daily_reminder(self):
        config = self._read_config()
        email_settings = self._get_email_settings(config)

        if not email_settings.get("enable_reminders", False):
            print("Email reminders are disabled.")
            return

        reminder_time = email_settings.get("reminder_time", "09:00")
        hour, minute = self._parse_reminder_time(reminder_time)

        try:
            self.scheduler.remove_job("daily_email_reminder")
        except Exception:
            pass

        try:
            self.scheduler.add_job(
                self._send_daily_reminder_task,
                trigger=CronTrigger(hour=hour, minute=minute),
                id="daily_email_reminder",
                name="daily_email_reminder",
                replace_existing=True,
            )
            print(f"Daily email reminder scheduled for {reminder_time}.")
        except Exception as e:
            print(f"Failed to schedule daily email reminder: {e}")

    def _should_send_catchup_today(self, config: dict) -> bool:
        email_settings = self._get_email_settings(config)
        if not email_settings.get("enable_reminders", False):
            return False

        reminder_time = email_settings.get("reminder_time", "09:00")
        hour, minute = self._parse_reminder_time(reminder_time)
        now = datetime.now()
        scheduled_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if now < scheduled_today:
            return False

        if email_settings.get("last_sent_date") == now.strftime("%Y-%m-%d"):
            return False

        return True

    def _send_missed_reminder_if_needed(self):
        try:
            config = self._read_config()
            if not self._should_send_catchup_today(config):
                return

            result = self._send_daily_reminder_task(trigger_source="startup_catchup")
            if result.get("success"):
                print("Sent startup catch-up reminder email.")
        except Exception as e:
            print(f"Failed to send startup catch-up reminder: {e}")

    def _send_daily_reminder_task(self, trigger_source: str = "scheduled") -> dict:
        try:
            config = self._read_config()
            user_info = config.get("user_info", {})
            email_settings = self._get_email_settings(config)

            if not email_settings.get("enable_reminders", False):
                return {"success": False, "error": "Email reminders are disabled"}

            recipient_email = user_info.get("email")
            user_name = user_info.get("name", "User")
            sender_email = email_settings.get("sender_email")
            app_password = email_settings.get("app_password")

            if not recipient_email or not sender_email or not app_password:
                return {"success": False, "error": "Email configuration is incomplete"}

            review_manager = ReviewManager(self.data_dir)
            today_reviews = review_manager.get_today_review_list()
            if not today_reviews:
                return {"success": False, "error": "No review words are due right now"}

            email_body = EmailManager.generate_daily_review_email(
                user_name=user_name,
                review_words=today_reviews,
            )

            result = EmailManager.send_email(
                smtp_server=email_settings.get("smtp_server", "smtp.gmail.com"),
                smtp_port=email_settings.get("smtp_port", 587),
                sender_email=sender_email,
                sender_password=app_password,
                recipient_email=recipient_email,
                subject=f"{len(today_reviews)} words due for review",
                body=email_body,
                is_html=True,
            )

            if result.get("success"):
                today = datetime.now().strftime("%Y-%m-%d")
                self._mark_reminder_sent(config, today)
                print(f"Reminder email sent to {recipient_email} via {trigger_source}.")

            return result
        except Exception as e:
            print(f"Failed to send reminder email: {e}")
            return {"success": False, "error": str(e)}

    def add_custom_job(
        self,
        func: Callable,
        trigger_type: str = "cron",
        job_id: Optional[str] = None,
        **trigger_kwargs,
    ):
        try:
            if trigger_type == "cron":
                trigger = CronTrigger(**trigger_kwargs)
            elif trigger_type == "interval":
                from apscheduler.triggers.interval import IntervalTrigger

                trigger = IntervalTrigger(**trigger_kwargs)
            elif trigger_type == "date":
                from apscheduler.triggers.date import DateTrigger

                trigger = DateTrigger(**trigger_kwargs)
            else:
                print(f"Unknown trigger type: {trigger_type}")
                return

            self.scheduler.add_job(func, trigger=trigger, id=job_id, replace_existing=True)
            print(f"Added job {job_id}.")
        except Exception as e:
            print(f"Failed to add job: {e}")

    def update_reminder_settings(self, reminder_time: str):
        config = self._read_config()
        email_settings = self._get_email_settings(config)
        email_settings["reminder_time"] = reminder_time
        self._write_config(config)
        self._schedule_daily_reminder()

    def get_scheduled_jobs(self):
        return self.scheduler.get_jobs()

    def remove_job(self, job_id: str) -> bool:
        try:
            self.scheduler.remove_job(job_id)
            print(f"Removed job {job_id}.")
            return True
        except Exception as e:
            print(f"Failed to remove job: {e}")
            return False


_scheduler_instance = None


def get_scheduler(data_dir: str = "backend/data") -> ReviewScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ReviewScheduler(data_dir)
    return _scheduler_instance
