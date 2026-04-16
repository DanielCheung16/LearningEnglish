import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SpacedRepetitionAlgorithm:
    """
    FSRS-lite scheduler.

    This is not a full implementation of official FSRS. It keeps the same
    high-level ideas:
    - Stability: how long the memory can survive before recall drops.
    - Difficulty: how hard the item is for the learner.
    - Retrievability: estimated recall probability at the current moment.
    - Lapses: how many failures the item has accumulated.

    The model is intentionally simplified so it fits the current project
    without requiring trained parameters.
    """

    STEP_INTERVALS = [
        timedelta(hours=3),
        timedelta(hours=5),
        timedelta(days=1),
        timedelta(days=3),
        timedelta(days=7),
        timedelta(days=15),
        timedelta(days=30),
        timedelta(days=60),
    ]

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DATE_FORMAT = "%Y-%m-%d"
    DEFAULT_DESIRED_RETENTION = 0.9

    PROFICIENCY_LEVELS = {
        "unfamiliar": {"name": "不熟悉", "factor": 0.5, "weight": 0},
        "familiar": {"name": "熟悉", "factor": 1.0, "weight": 25},
        "practiced": {"name": "练习中", "factor": 1.3, "weight": 50},
        "mastered": {"name": "已掌握", "factor": 1.5, "weight": 100},
    }

    SUCCESS_LEVELS = {"familiar", "practiced", "mastered"}

    @staticmethod
    def now() -> datetime:
        return datetime.now()

    @staticmethod
    def format_review_time(value: datetime) -> str:
        return value.strftime(SpacedRepetitionAlgorithm.DATETIME_FORMAT)

    @staticmethod
    def parse_review_time(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            pass

        for fmt in (
            SpacedRepetitionAlgorithm.DATETIME_FORMAT,
            SpacedRepetitionAlgorithm.DATE_FORMAT,
        ):
            try:
                return datetime.strptime(value, fmt)
            except (ValueError, TypeError):
                continue
        return None

    @staticmethod
    def interval_to_days(interval: timedelta) -> float:
        return interval.total_seconds() / 86400

    @staticmethod
    def days_to_interval(days: float) -> timedelta:
        return timedelta(days=max(days, 1 / 1440))

    @staticmethod
    def get_step_days(index: int) -> float:
        bounded_index = max(0, min(index, len(SpacedRepetitionAlgorithm.STEP_INTERVALS) - 1))
        return SpacedRepetitionAlgorithm.interval_to_days(
            SpacedRepetitionAlgorithm.STEP_INTERVALS[bounded_index]
        )

    @staticmethod
    def create_initial_state() -> Dict[str, float]:
        return {
            "stability": SpacedRepetitionAlgorithm.get_step_days(0),
            "difficulty": 5.0,
            "retrievability": 1.0,
            "lapses": 0,
            "desired_retention": SpacedRepetitionAlgorithm.DEFAULT_DESIRED_RETENTION,
            "state": "learning",
        }

    @staticmethod
    def estimate_retrievability(stability: float, elapsed_days: float) -> float:
        stability = max(stability, 1 / 1440)
        elapsed_days = max(elapsed_days, 0.0)
        recall = math.exp(math.log(0.9) * (elapsed_days / stability))
        return min(1.0, max(0.0, recall))

    @staticmethod
    def calculate_next_review_date(
        current_review_count: int,
        proficiency_level: str,
        last_review_date: str = None,
        add_days: int = 0,
    ) -> str:
        state = SpacedRepetitionAlgorithm.create_initial_state()
        state["stability"] = SpacedRepetitionAlgorithm.get_step_days(current_review_count)
        updated_state, next_review = SpacedRepetitionAlgorithm.update_state(
            fsrs_state=state,
            current_review_count=current_review_count,
            proficiency_level=proficiency_level,
            last_review_date=last_review_date,
        )
        next_review = next_review + timedelta(days=add_days)
        return SpacedRepetitionAlgorithm.format_review_time(next_review)

    @staticmethod
    def update_state(
        fsrs_state: Optional[Dict],
        current_review_count: int,
        proficiency_level: str,
        last_review_date: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> (Dict, datetime):
        now = now or SpacedRepetitionAlgorithm.now()
        state = dict(SpacedRepetitionAlgorithm.create_initial_state())
        if fsrs_state:
            state.update(fsrs_state)

        last_review = SpacedRepetitionAlgorithm.parse_review_time(last_review_date)
        elapsed_days = (
            max((now - last_review).total_seconds(), 0) / 86400 if last_review else 0.0
        )
        current_stability = max(float(state.get("stability", SpacedRepetitionAlgorithm.get_step_days(0))), 1 / 1440)
        current_difficulty = min(max(float(state.get("difficulty", 5.0)), 1.0), 10.0)
        current_lapses = int(state.get("lapses", 0))
        retrievability = SpacedRepetitionAlgorithm.estimate_retrievability(
            current_stability,
            elapsed_days,
        )

        if proficiency_level == "unfamiliar":
            new_lapses = current_lapses + 1
            lapse_penalty = 0.2 if elapsed_days > (current_stability * 0.6) else 0.12
            new_stability = max(
                SpacedRepetitionAlgorithm.get_step_days(0),
                current_stability * lapse_penalty,
            )
            new_difficulty = min(10.0, current_difficulty + 0.9)
            state_name = "relearning"
        else:
            growth_base = {
                "familiar": 1.35,
                "practiced": 1.9,
                "mastered": 2.45,
            }[proficiency_level]
            difficulty_bonus = max(0.6, 1.18 - ((current_difficulty - 5.0) * 0.06))
            retrieval_bonus = 1.0 + ((1.0 - retrievability) * 0.45)
            spacing_bonus = 1.0 + min(elapsed_days / max(current_stability, 0.1), 1.5) * 0.08
            new_stability = current_stability * growth_base * difficulty_bonus * retrieval_bonus * spacing_bonus

            # Keep early repetitions aligned with the configured bootstrap intervals.
            bootstrap_days = SpacedRepetitionAlgorithm.get_step_days(current_review_count + 1)
            new_stability = max(new_stability, bootstrap_days)

            difficulty_shift = {
                "familiar": 0.15,
                "practiced": -0.25,
                "mastered": -0.45,
            }[proficiency_level]
            new_difficulty = min(10.0, max(1.0, current_difficulty + difficulty_shift))
            new_lapses = current_lapses
            state_name = "review"

        next_review = now + SpacedRepetitionAlgorithm.days_to_interval(new_stability)
        next_retrievability = 1.0

        state.update({
            "stability": round(new_stability, 4),
            "difficulty": round(new_difficulty, 2),
            "retrievability": round(next_retrievability, 4),
            "lapses": new_lapses,
            "desired_retention": state.get(
                "desired_retention",
                SpacedRepetitionAlgorithm.DEFAULT_DESIRED_RETENTION,
            ),
            "state": "leech" if new_lapses >= 8 else state_name,
        })
        return state, next_review

    @staticmethod
    def calculate_master_level(review_history: List[Dict], fsrs_state: Optional[Dict] = None) -> float:
        if not review_history and not fsrs_state:
            return 0

        fsrs_state = fsrs_state or {}
        stability = float(fsrs_state.get("stability", SpacedRepetitionAlgorithm.get_step_days(0)))
        difficulty = float(fsrs_state.get("difficulty", 5.0))
        retrievability = float(fsrs_state.get("retrievability", 1.0))
        lapses = int(fsrs_state.get("lapses", 0))

        recent_reviews = review_history[-5:] if review_history else []
        recent_score = 0.0
        if recent_reviews:
            recent_score = sum(
                SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS.get(
                    item.get("proficiency", "unfamiliar"),
                    {"weight": 0},
                )["weight"]
                for item in recent_reviews
            ) / len(recent_reviews)

        stability_score = min(stability / 30.0, 1.0) * 45.0
        retrieval_score = min(max(retrievability, 0.0), 1.0) * 20.0
        difficulty_score = ((10.0 - min(max(difficulty, 1.0), 10.0)) / 9.0) * 15.0
        history_score = (recent_score / 100.0) * 25.0
        lapse_penalty = min(lapses * 4.0, 20.0)

        mastery = stability_score + retrieval_score + difficulty_score + history_score - lapse_penalty
        return round(min(100.0, max(0.0, mastery)), 1)

    @staticmethod
    def should_review_today(next_review_date: str) -> bool:
        review_time = SpacedRepetitionAlgorithm.parse_review_time(next_review_date)
        if not review_time:
            return False
        return review_time <= SpacedRepetitionAlgorithm.now()

    @staticmethod
    def get_days_until_review(next_review_date: str) -> int:
        review_time = SpacedRepetitionAlgorithm.parse_review_time(next_review_date)
        if not review_time:
            return 0
        delta = review_time - SpacedRepetitionAlgorithm.now()
        return delta.days

    @staticmethod
    def get_proficiency_name(level: str) -> str:
        return SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS.get(level, {"name": "未知"})["name"]

    @staticmethod
    def get_all_proficiency_levels() -> Dict[str, Dict]:
        return SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS
