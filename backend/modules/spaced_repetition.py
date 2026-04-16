from datetime import datetime, timedelta
from typing import Dict, Optional, List
import math

class SpacedRepetitionAlgorithm:
    """
    艾宾浩斯遗忘曲线算法实现

    复习间隔: 1天 → 3天 → 7天 → 15天 → 30天 → 60天
    """

    # 标准艾宾浩斯间隔（天数）
    INTERVALS = [1, 3, 7, 15, 30, 60]

    # 掌握程度对应的名称和难度系数
    PROFICIENCY_LEVELS = {
        "unfamiliar": {
            "name": "不熟悉",
            "factor": 0.5,      # 遗忘，重新开始
            "weight": 0
        },
        "familiar": {
            "name": "熟悉",
            "factor": 1.0,      # 按标准间隔
            "weight": 25
        },
        "practiced": {
            "name": "练习中",
            "factor": 1.3,      # 间隔拉长30%
            "weight": 50
        },
        "mastered": {
            "name": "已掌握",
            "factor": 1.5,      # 间隔拉长50%
            "weight": 100
        }
    }

    @staticmethod
    def calculate_next_review_date(
        current_review_count: int,
        proficiency_level: str,
        last_review_date: str = None,
        add_days: int = 0
    ) -> str:
        """
        计算下一次复习日期

        参数:
            current_review_count: 当前已复习次数（0表示新词）
            proficiency_level: 掌握程度 (unfamiliar/familiar/practiced/mastered)
            last_review_date: 上次复习日期 (YYYY-MM-DD)
            add_days: 额外增加的天数

        返回:
            下一次复习日期 (YYYY-MM-DD)
        """
        # 如果是新词（未复习过），下一次复习为明天
        if current_review_count == 0:
            next_date = datetime.now() + timedelta(days=1)
            return next_date.strftime("%Y-%m-%d")

        # 如果掌握程度是"不熟悉"，重新开始（从第1个间隔开始）
        if proficiency_level == "unfamiliar":
            next_date = datetime.now() + timedelta(days=SpacedRepetitionAlgorithm.INTERVALS[0])
            return next_date.strftime("%Y-%m-%d")

        # 获取难度系数
        factor = SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS[proficiency_level]["factor"]

        # 根据复习次数确定间隔索引
        # current_review_count是已完成的复习次数，下一次应该用第current_review_count个间隔
        if current_review_count >= len(SpacedRepetitionAlgorithm.INTERVALS):
            # 如果已经超过最大间隔次数，使用最后一个间隔
            interval_days = SpacedRepetitionAlgorithm.INTERVALS[-1]
        else:
            interval_days = SpacedRepetitionAlgorithm.INTERVALS[current_review_count]

        # 根据掌握程度调整间隔
        adjusted_interval = int(interval_days * factor)

        # 从现在开始计算（而不是从上次复习日期）
        next_date = datetime.now() + timedelta(days=adjusted_interval + add_days)

        return next_date.strftime("%Y-%m-%d")

    @staticmethod
    def calculate_master_level(review_history: List[Dict]) -> float:
        """
        根据复习历史计算掌握程度（0-100%）

        参数:
            review_history: 复习记录列表，每条包含 {"proficiency": "...", "review_date": "..."}

        返回:
            掌握程度百分比 (0-100)
        """
        if not review_history:
            return 0

        total_weight = 0
        for record in review_history:
            proficiency = record.get("proficiency", "unfamiliar")
            weight = SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS.get(
                proficiency, {"weight": 0}
            )["weight"]
            total_weight += weight

        # 计算平均掌握程度，但考虑最近的复习权重更高
        # 使用指数加权平均
        if len(review_history) == 0:
            return 0

        latest_weight = SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS.get(
            review_history[-1].get("proficiency", "unfamiliar"),
            {"weight": 0}
        )["weight"]

        # 简单方式：取最近5次复习的平均值
        recent_reviews = review_history[-5:]
        recent_weight = sum([
            SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS.get(
                r.get("proficiency", "unfamiliar"),
                {"weight": 0}
            )["weight"] for r in recent_reviews
        ]) / len(recent_reviews)

        # 最终掌握度 = 最近复习的权重 * 0.7 + 历史平均 * 0.3
        master_level = recent_weight * 0.7 + (total_weight / len(review_history) / 100) * 30

        return min(100, max(0, master_level))

    @staticmethod
    def should_review_today(next_review_date: str) -> bool:
        """
        检查是否需要在今天复习

        参数:
            next_review_date: 下次复习日期 (YYYY-MM-DD)

        返回:
            True 如果需要今天复习
        """
        try:
            review_date = datetime.strptime(next_review_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            return review_date <= today
        except (ValueError, TypeError):
            return False

    @staticmethod
    def get_days_until_review(next_review_date: str) -> int:
        """
        计算距离下次复习还有多少天

        参数:
            next_review_date: 下次复习日期 (YYYY-MM-DD)

        返回:
            天数（负数表示已逾期）
        """
        try:
            review_date = datetime.strptime(next_review_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            delta = (review_date - today).days
            return delta
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def get_proficiency_name(level: str) -> str:
        """获取掌握程度的中文名称"""
        return SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS.get(
            level, {"name": "未知"}
        )["name"]

    @staticmethod
    def get_all_proficiency_levels() -> Dict[str, Dict]:
        """获取所有掌握程度及其描述"""
        return SpacedRepetitionAlgorithm.PROFICIENCY_LEVELS


# 使用示例
if __name__ == "__main__":
    # 测试新词添加
    new_word_next_review = SpacedRepetitionAlgorithm.calculate_next_review_date(
        current_review_count=0,
        proficiency_level="familiar"
    )
    print(f"新词下次复习日期: {new_word_next_review}")

    # 测试第1次复习后
    review1_next = SpacedRepetitionAlgorithm.calculate_next_review_date(
        current_review_count=1,
        proficiency_level="familiar"
    )
    print(f"第1次review后（familiar）: {review1_next}")

    # 测试第1次复习后，但掌握程度为"practiced"
    review1_practiced = SpacedRepetitionAlgorithm.calculate_next_review_date(
        current_review_count=1,
        proficiency_level="practiced"
    )
    print(f"第1次review后（practiced）: {review1_practiced}")

    # 测试掌握度计算
    history = [
        {"proficiency": "familiar", "review_date": "2024-01-01"},
        {"proficiency": "practiced", "review_date": "2024-01-04"},
        {"proficiency": "practiced", "review_date": "2024-01-11"},
        {"proficiency": "mastered", "review_date": "2024-01-26"}
    ]
    master_level = SpacedRepetitionAlgorithm.calculate_master_level(history)
    print(f"掌握度: {master_level:.1f}%")
