import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "backend" / "data"


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    now = datetime.now().isoformat()

    write_json(
        DATA_DIR / "words.json",
        {
            "metadata": {
                "version": "1.0",
                "created_date": now,
                "total_words": 0,
                "last_sync": now,
            },
            "words": [],
        },
    )

    write_json(
        DATA_DIR / "review_schedule.json",
        {
            "review_records": [],
        },
    )

    write_json(
        DATA_DIR / "user_config.json",
        {
            "user_info": {
                "email": "",
                "name": "",
            },
            "email_settings": {
                "enable_reminders": False,
                "reminder_frequency": "daily",
                "reminder_time": "09:00",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "app_password": "",
                "last_sent_date": "",
            },
            "review_settings": {
                "intervals": [1, 3, 7, 15, 30, 60],
            },
        },
    )

    print("Initialized empty local data files in backend/data")


if __name__ == "__main__":
    main()
