import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from .spaced_repetition import SpacedRepetitionAlgorithm


class ReviewManager:
    """Manage review records using an FSRS-lite compatible state model."""

    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = data_dir
        self.review_file = os.path.join(data_dir, "review_schedule.json")
        self._ensure_review_file()

    def _ensure_review_file(self):
        if not os.path.exists(self.review_file):
            self._write_json(self.review_file, {"review_records": []})

    def _read_json(self, filepath: str) -> Dict:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_json(self, filepath: str, data: Dict):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_review_data(self) -> Dict:
        review_data = self._read_json(self.review_file)
        review_data.setdefault("review_records", [])
        changed = False

        for index, record in enumerate(review_data["review_records"]):
            normalized = self._normalize_record(record)
            if normalized != record:
                review_data["review_records"][index] = normalized
                changed = True

        if changed:
            self._write_json(self.review_file, review_data)

        return review_data

    def _normalize_record(self, record: Dict) -> Dict:
        normalized = dict(record)
        normalized.setdefault("review_dates", [])
        normalized.setdefault("review_count", len(normalized["review_dates"]))

        fsrs = dict(normalized.get("fsrs", {}))
        if not fsrs:
            fsrs = SpacedRepetitionAlgorithm.create_initial_state()
            fsrs["stability"] = SpacedRepetitionAlgorithm.get_step_days(
                max(int(normalized.get("review_count", 0)), 0)
            )
            fsrs["state"] = "learning" if normalized.get("review_count", 0) == 0 else "review"

        fsrs.setdefault("difficulty", 5.0)
        fsrs.setdefault("stability", SpacedRepetitionAlgorithm.get_step_days(0))
        fsrs.setdefault("retrievability", 1.0)
        fsrs.setdefault("lapses", normalized.get("lapse_count", 0))
        fsrs.setdefault("desired_retention", SpacedRepetitionAlgorithm.DEFAULT_DESIRED_RETENTION)
        fsrs.setdefault("state", "learning")

        last_review_date = normalized.get("last_review_date")
        parsed_last_review = SpacedRepetitionAlgorithm.parse_review_time(last_review_date)
        elapsed_days = 0.0
        if parsed_last_review:
            elapsed_days = max(
                (SpacedRepetitionAlgorithm.now() - parsed_last_review).total_seconds(),
                0.0,
            ) / 86400
        fsrs["retrievability"] = round(
            SpacedRepetitionAlgorithm.estimate_retrievability(
                float(fsrs["stability"]),
                elapsed_days,
            ),
            4,
        )

        normalized["fsrs"] = fsrs
        normalized["lapse_count"] = int(fsrs.get("lapses", 0))
        normalized["master_level"] = SpacedRepetitionAlgorithm.calculate_master_level(
            normalized["review_dates"],
            fsrs,
        )

        if fsrs.get("state") == "leech":
            normalized["status"] = "leech"
        elif normalized["master_level"] >= 85 and float(fsrs.get("stability", 0)) >= 15:
            normalized["status"] = "mastered"
        elif normalized.get("review_count", 0) > 0:
            normalized["status"] = "in_progress"
        else:
            normalized["status"] = "pending"

        if not normalized.get("next_review_date"):
            next_review_time = SpacedRepetitionAlgorithm.now() + SpacedRepetitionAlgorithm.days_to_interval(
                float(fsrs["stability"])
            )
            normalized["next_review_date"] = SpacedRepetitionAlgorithm.serialize_review_time(next_review_time)
        else:
            parsed_next = SpacedRepetitionAlgorithm.parse_review_time(normalized["next_review_date"])
            if parsed_next:
                normalized["next_review_date"] = SpacedRepetitionAlgorithm.serialize_review_time(parsed_next)

        return normalized

    def _find_record(self, review_data: Dict, word_id: str) -> Optional[Dict]:
        for record in review_data.get("review_records", []):
            if record.get("word_id") == word_id:
                return record
        return None

    def initialize_review_for_word(self, word_id: str, word: str) -> Dict:
        review_data = self._load_review_data()
        existing = self._find_record(review_data, word_id)
        if existing:
            return existing

        initial_state = SpacedRepetitionAlgorithm.create_initial_state()
        next_review_time = SpacedRepetitionAlgorithm.now() + SpacedRepetitionAlgorithm.days_to_interval(
            1
        )

        new_record = {
            "id": f"review_{uuid.uuid4().hex[:8]}",
            "word_id": word_id,
            "word": word,
            "review_count": 0,
            "review_dates": [],
            "next_review_date": SpacedRepetitionAlgorithm.serialize_review_time(next_review_time),
            "master_level": 0,
            "last_review_date": None,
            "status": "pending",
            "lapse_count": 0,
            "fsrs": initial_state,
        }

        review_data["review_records"].append(new_record)
        self._write_json(self.review_file, review_data)
        return new_record

    def get_today_review_list(self) -> List[Dict]:
        review_data = self._load_review_data()
        today_reviews = []

        for record in review_data.get("review_records", []):
            if record.get("status") == "mastered":
                continue
            if SpacedRepetitionAlgorithm.should_review_today(record.get("next_review_date")):
                today_reviews.append(record)

        today_reviews.sort(key=lambda x: x.get("next_review_date", "2099-12-31 23:59:59"))
        return today_reviews

    def _apply_review_outcome(self, record: Dict, proficiency_level: str, trigger: str = "review") -> Dict:
        now = SpacedRepetitionAlgorithm.now()
        now_str = now.isoformat()
        fsrs_state, next_review = SpacedRepetitionAlgorithm.update_state(
            fsrs_state=record.get("fsrs", {}),
            current_review_count=record.get("review_count", 0),
            proficiency_level=proficiency_level,
            last_review_date=record.get("last_review_date"),
            now=now,
        )

        record["review_count"] = record.get("review_count", 0) + 1
        record["last_review_date"] = now_str
        record.setdefault("review_dates", []).append({
            "proficiency": proficiency_level,
            "review_date": now_str,
            "scheduled_date": record.get("next_review_date"),
            "trigger": trigger,
        })
        record["fsrs"] = fsrs_state
        record["lapse_count"] = int(fsrs_state.get("lapses", 0))
        record["next_review_date"] = SpacedRepetitionAlgorithm.serialize_review_time(next_review)
        record["master_level"] = SpacedRepetitionAlgorithm.calculate_master_level(
            record["review_dates"],
            fsrs_state,
        )

        if fsrs_state.get("state") == "leech":
            record["status"] = "leech"
        elif record["master_level"] >= 85 and float(fsrs_state.get("stability", 0)) >= 15:
            record["status"] = "mastered"
        else:
            record["status"] = "in_progress"

        return record

    def submit_review(self, word_id: str, proficiency_level: str) -> Dict:
        review_data = self._load_review_data()
        record = self._find_record(review_data, word_id)
        if not record:
            return {"success": False, "error": f"Word ID {word_id} not found"}

        self._apply_review_outcome(record, proficiency_level, trigger="review")
        self._write_json(self.review_file, review_data)
        return {
            "success": True,
            "record": record,
            "next_review_date": record["next_review_date"],
            "master_level": record["master_level"],
            "status": record["status"],
            "fsrs": record["fsrs"],
        }

    def penalize_duplicate_word(self, word_id: str) -> Dict:
        review_data = self._load_review_data()
        record = self._find_record(review_data, word_id)
        if not record:
            return {"success": False, "error": f"Word ID {word_id} not found"}

        self._apply_review_outcome(record, "unfamiliar", trigger="duplicate_add")
        self._write_json(self.review_file, review_data)
        return {
            "success": True,
            "record": record,
            "next_review_date": record["next_review_date"],
            "master_level": record["master_level"],
            "status": record["status"],
            "fsrs": record["fsrs"],
        }

    def get_review_history(self, word_id: str) -> Optional[Dict]:
        review_data = self._load_review_data()
        return self._find_record(review_data, word_id)

    def get_review_stats(self) -> Dict:
        review_data = self._load_review_data()
        records = review_data.get("review_records", [])

        total_words = len(records)
        mastered_count = sum(1 for r in records if r.get("status") == "mastered")
        in_progress_count = sum(1 for r in records if r.get("status") == "in_progress")
        pending_count = sum(1 for r in records if r.get("status") == "pending")
        leech_count = sum(1 for r in records if r.get("status") == "leech")
        today_reviews = self.get_today_review_list()

        avg_review_count = sum(r.get("review_count", 0) for r in records) / max(total_words, 1)
        avg_master_level = sum(r.get("master_level", 0) for r in records) / max(total_words, 1)

        return {
            "total_words": total_words,
            "mastered_count": mastered_count,
            "in_progress_count": in_progress_count,
            "pending_count": pending_count,
            "leech_count": leech_count,
            "today_review_count": len(today_reviews),
            "average_review_count": round(avg_review_count, 2),
            "average_master_level": round(avg_master_level, 1),
            "progress_percentage": round(mastered_count / max(total_words, 1) * 100, 1),
        }

    def get_review_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        review_data = self._load_review_data()
        filtered_records = []

        for record in review_data.get("review_records", []):
            for review_entry in record.get("review_dates", []):
                review_date = review_entry.get("review_date", "")[:10]
                if start_date <= review_date <= end_date:
                    filtered_records.append(record)
                    break

        return filtered_records

    def delete_review_record(self, word_id: str) -> bool:
        review_data = self._load_review_data()
        original_count = len(review_data.get("review_records", []))
        review_data["review_records"] = [
            r for r in review_data.get("review_records", []) if r.get("word_id") != word_id
        ]

        if len(review_data["review_records"]) < original_count:
            self._write_json(self.review_file, review_data)
            return True
        return False

    def delete_review_records(self, word_ids: List[str]) -> int:
        target_ids = {word_id for word_id in word_ids if word_id}
        if not target_ids:
            return 0

        review_data = self._load_review_data()
        original_count = len(review_data.get("review_records", []))
        review_data["review_records"] = [
            record
            for record in review_data.get("review_records", [])
            if record.get("word_id") not in target_ids
        ]

        deleted_count = original_count - len(review_data["review_records"])
        if deleted_count:
            self._write_json(self.review_file, review_data)
        return deleted_count

    def reset_word_review(self, word_id: str) -> bool:
        review_data = self._load_review_data()
        record = self._find_record(review_data, word_id)
        if not record:
            return False

        initial_state = SpacedRepetitionAlgorithm.create_initial_state()
        next_review_time = SpacedRepetitionAlgorithm.now()
        record["review_count"] = 0
        record["review_dates"] = []
        record["next_review_date"] = SpacedRepetitionAlgorithm.serialize_review_time(next_review_time)
        record["master_level"] = 0
        record["last_review_date"] = None
        record["status"] = "pending"
        record["lapse_count"] = 0
        record["fsrs"] = initial_state

        self._write_json(self.review_file, review_data)
        return True

    def get_overdue_reviews(self) -> List[Dict]:
        review_data = self._load_review_data()
        overdue_reviews = []
        now = SpacedRepetitionAlgorithm.now()

        for record in review_data.get("review_records", []):
            if record.get("status") == "mastered":
                continue
            next_review_date = SpacedRepetitionAlgorithm.parse_review_time(record.get("next_review_date"))
            if next_review_date and next_review_date < now:
                overdue_reviews.append(record)

        overdue_reviews.sort(key=lambda x: x.get("next_review_date", "2099-12-31 23:59:59"))
        return overdue_reviews
