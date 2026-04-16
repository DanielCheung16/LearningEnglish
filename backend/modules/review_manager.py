import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid
from .spaced_repetition import SpacedRepetitionAlgorithm


class ReviewManager:
    """管理复习计划和复习记录"""

    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = data_dir
        self.review_file = os.path.join(data_dir, "review_schedule.json")
        self._ensure_review_file()

    def _ensure_review_file(self):
        """确保复习文件存在"""
        if not os.path.exists(self.review_file):
            default_data = {
                "review_records": []
            }
            self._write_json(self.review_file, default_data)

    def _read_json(self, filepath: str) -> Dict:
        """读取JSON文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_json(self, filepath: str, data: Dict):
        """写入JSON文件"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def initialize_review_for_word(self, word_id: str, word: str) -> Dict:
        """
        为新添加的单词初始化复习记录

        参数:
            word_id: 单词ID
            word: 单词文本

        返回:
            创建的复习记录
        """
        review_data = self._read_json(self.review_file)

        # 检查是否已存在
        for record in review_data["review_records"]:
            if record["word_id"] == word_id:
                return record

        # 计算下一次复习日期（明天）
        next_review_date = SpacedRepetitionAlgorithm.calculate_next_review_date(
            current_review_count=0,
            proficiency_level="familiar"
        )

        new_record = {
            "id": f"review_{uuid.uuid4().hex[:8]}",
            "word_id": word_id,
            "word": word,
            "review_count": 0,
            "review_dates": [],
            "next_review_date": next_review_date,
            "master_level": 0,
            "last_review_date": None,
            "status": "pending"  # pending, in_progress, mastered
        }

        review_data["review_records"].append(new_record)
        self._write_json(self.review_file, review_data)

        return new_record

    def get_today_review_list(self) -> List[Dict]:
        """
        获取今日需要复习的单词列表

        返回:
            今日需要复习的review记录列表
        """
        review_data = self._read_json(self.review_file)
        today_reviews = []

        for record in review_data["review_records"]:
            if record["status"] != "mastered":
                next_review_date = record.get("next_review_date")
                if SpacedRepetitionAlgorithm.should_review_today(next_review_date):
                    today_reviews.append(record)

        # 按next_review_date排序（最逾期的先复习）
        today_reviews.sort(
            key=lambda x: x.get("next_review_date", "2099-12-31")
        )

        return today_reviews

    def submit_review(self, word_id: str, proficiency_level: str) -> Dict:
        """
        提交复习结果，更新下一次复习日期

        参数:
            word_id: 单词ID
            proficiency_level: 掌握程度 (unfamiliar/familiar/practiced/mastered)

        返回:
            更新后的复习记录
        """
        review_data = self._read_json(self.review_file)

        for record in review_data["review_records"]:
            if record["word_id"] == word_id:
                # 更新复习记录
                now = datetime.now().isoformat()
                record["review_count"] = record.get("review_count", 0) + 1
                record["last_review_date"] = now

                # 记录本次复习
                review_entry = {
                    "proficiency": proficiency_level,
                    "review_date": now,
                    "scheduled_date": record.get("next_review_date")
                }
                record["review_dates"].append(review_entry)

                # 计算下一次复习日期
                record["next_review_date"] = SpacedRepetitionAlgorithm.calculate_next_review_date(
                    current_review_count=record["review_count"],
                    proficiency_level=proficiency_level
                )

                # 计算掌握程度
                record["master_level"] = SpacedRepetitionAlgorithm.calculate_master_level(
                    record["review_dates"]
                )

                # 判断是否已掌握（掌握程度>=75%）
                if record["master_level"] >= 75 and proficiency_level in ["practiced", "mastered"]:
                    record["status"] = "mastered"
                else:
                    record["status"] = "in_progress"

                self._write_json(self.review_file, review_data)

                return {
                    "success": True,
                    "record": record,
                    "next_review_date": record["next_review_date"],
                    "master_level": record["master_level"],
                    "status": record["status"]
                }

        return {
            "success": False,
            "error": f"单词ID {word_id} 不存在"
        }

    def get_review_history(self, word_id: str) -> Optional[Dict]:
        """
        获取单词的复习历史

        参数:
            word_id: 单词ID

        返回:
            该单词的完整复习记录
        """
        review_data = self._read_json(self.review_file)

        for record in review_data["review_records"]:
            if record["word_id"] == word_id:
                return record

        return None

    def get_review_stats(self) -> Dict:
        """
        获取复习统计信息

        返回:
            统计数据
        """
        review_data = self._read_json(self.review_file)
        records = review_data["review_records"]

        total_words = len(records)
        mastered_count = sum(1 for r in records if r["status"] == "mastered")
        in_progress_count = sum(1 for r in records if r["status"] == "in_progress")
        pending_count = sum(1 for r in records if r["status"] == "pending")

        today_reviews = self.get_today_review_list()

        avg_review_count = sum(r.get("review_count", 0) for r in records) / max(total_words, 1)
        avg_master_level = sum(r.get("master_level", 0) for r in records) / max(total_words, 1)

        return {
            "total_words": total_words,
            "mastered_count": mastered_count,
            "in_progress_count": in_progress_count,
            "pending_count": pending_count,
            "today_review_count": len(today_reviews),
            "average_review_count": round(avg_review_count, 2),
            "average_master_level": round(avg_master_level, 1),
            "progress_percentage": round(mastered_count / max(total_words, 1) * 100, 1)
        }

    def get_review_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        获取某日期范围内复习过的单词

        参数:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        返回:
            复习记录列表
        """
        review_data = self._read_json(self.review_file)
        filtered_records = []

        for record in review_data["review_records"]:
            for review_entry in record.get("review_dates", []):
                review_date = review_entry.get("review_date", "")[:10]
                if start_date <= review_date <= end_date:
                    filtered_records.append(record)
                    break

        return filtered_records

    def delete_review_record(self, word_id: str) -> bool:
        """
        删除某单词的复习记录（通常在删除单词时调用）

        参数:
            word_id: 单词ID

        返回:
            是否成功删除
        """
        review_data = self._read_json(self.review_file)
        original_count = len(review_data["review_records"])

        review_data["review_records"] = [
            r for r in review_data["review_records"] if r["word_id"] != word_id
        ]

        if len(review_data["review_records"]) < original_count:
            self._write_json(self.review_file, review_data)
            return True

        return False

    def reset_word_review(self, word_id: str) -> bool:
        """
        重置单词的复习进度（将其回到初始状态）

        参数:
            word_id: 单词ID

        返回:
            是否成功重置
        """
        review_data = self._read_json(self.review_file)

        for record in review_data["review_records"]:
            if record["word_id"] == word_id:
                # 重置为初始状态
                next_review_date = SpacedRepetitionAlgorithm.calculate_next_review_date(
                    current_review_count=0,
                    proficiency_level="familiar"
                )

                record["review_count"] = 0
                record["review_dates"] = []
                record["next_review_date"] = next_review_date
                record["master_level"] = 0
                record["last_review_date"] = None
                record["status"] = "pending"

                self._write_json(self.review_file, review_data)
                return True

        return False

    def get_overdue_reviews(self) -> List[Dict]:
        """
        获取已逾期的复习（即应该今天或更早复习但还没做的）

        返回:
            逾期复习记录列表
        """
        review_data = self._read_json(self.review_file)
        overdue_reviews = []

        today = datetime.now().strftime("%Y-%m-%d")

        for record in review_data["review_records"]:
            if record["status"] != "mastered":
                next_review_date = record.get("next_review_date")
                if next_review_date and next_review_date < today:
                    overdue_reviews.append(record)

        # 按逾期天数排序
        overdue_reviews.sort(
            key=lambda x: x.get("next_review_date", "2099-12-31")
        )

        return overdue_reviews
