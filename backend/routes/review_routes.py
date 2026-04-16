from flask import Blueprint, request, jsonify
from backend.modules.review_manager import ReviewManager
from backend.modules.word_manager import WordManager

review_bp = Blueprint('review', __name__, url_prefix='/api/review')

# 初始化管理器
review_manager = ReviewManager()
word_manager = WordManager()


@review_bp.route('/today', methods=['GET'])
def get_today_review_list():
    """获取今日需要复习的单词列表"""
    try:
        today_reviews = review_manager.get_today_review_list()

        # 获取完整的单词信息
        enriched_reviews = []
        for review_record in today_reviews:
            word_id = review_record.get("word_id")
            word = word_manager.get_word_by_id(word_id)

            if word:
                enriched_review = {
                    **review_record,
                    "word_detail": word
                }
                enriched_reviews.append(enriched_review)

        return jsonify({
            "success": True,
            "data": enriched_reviews,
            "count": len(enriched_reviews)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@review_bp.route('/submit', methods=['POST'])
def submit_review():
    """
    提交复习结果

    请求体:
    {
        "word_id": "word_xxxxx",
        "proficiency_level": "familiar|practiced|mastered|unfamiliar"
    }
    """
    try:
        data = request.get_json()
        word_id = data.get("word_id")
        proficiency_level = data.get("proficiency_level", "familiar")

        if not word_id:
            return jsonify({
                "success": False,
                "error": "word_id不能为空"
            }), 400

        # 验证掌握程度
        valid_levels = ["unfamiliar", "familiar", "practiced", "mastered"]
        if proficiency_level not in valid_levels:
            return jsonify({
                "success": False,
                "error": f"无效的掌握程度，应为: {', '.join(valid_levels)}"
            }), 400

        result = review_manager.submit_review(word_id, proficiency_level)

        if result.get("success"):
            # 获取单词信息用于返回
            word = word_manager.get_word_by_id(word_id)

            return jsonify({
                "success": True,
                "message": "复习结果已保存",
                "next_review_date": result.get("next_review_date"),
                "master_level": result.get("master_level"),
                "status": result.get("status"),
                "word": word
            })
        else:
            return jsonify(result), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@review_bp.route('/history/<word_id>', methods=['GET'])
def get_review_history(word_id):
    """获取某单词的复习历史"""
    try:
        review_record = review_manager.get_review_history(word_id)

        if review_record:
            word = word_manager.get_word_by_id(word_id)

            return jsonify({
                "success": True,
                "word": word,
                "review_history": review_record
            })
        else:
            return jsonify({
                "success": False,
                "error": f"单词ID {word_id} 的复习记录不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@review_bp.route('/stats', methods=['GET'])
def get_review_stats():
    """获取复习统计信息"""
    try:
        stats = review_manager.get_review_stats()

        return jsonify({
            "success": True,
            "data": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@review_bp.route('/overdue', methods=['GET'])
def get_overdue_reviews():
    """获取已逾期的复习"""
    try:
        overdue_reviews = review_manager.get_overdue_reviews()

        # 获取完整的单词信息
        enriched_reviews = []
        for review_record in overdue_reviews:
            word_id = review_record.get("word_id")
            word = word_manager.get_word_by_id(word_id)

            if word:
                enriched_review = {
                    **review_record,
                    "word_detail": word
                }
                enriched_reviews.append(enriched_review)

        return jsonify({
            "success": True,
            "data": enriched_reviews,
            "count": len(enriched_reviews)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@review_bp.route('/reset/<word_id>', methods=['POST'])
def reset_word_review(word_id):
    """
    重置单词的复习进度

    用于想重新开始学习某个单词的情况
    """
    try:
        if review_manager.reset_word_review(word_id):
            review_record = review_manager.get_review_history(word_id)

            return jsonify({
                "success": True,
                "message": "复习进度已重置",
                "review_record": review_record
            })
        else:
            return jsonify({
                "success": False,
                "error": f"单词ID {word_id} 不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@review_bp.route('/by-date', methods=['GET'])
def get_review_by_date():
    """
    获取某日期范围内复习过的单词

    查询参数:
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({
                "success": False,
                "error": "start_date 和 end_date 不能为空"
            }), 400

        records = review_manager.get_review_by_date_range(start_date, end_date)

        # 获取完整的单词信息
        enriched_records = []
        for review_record in records:
            word_id = review_record.get("word_id")
            word = word_manager.get_word_by_id(word_id)

            if word:
                enriched_record = {
                    **review_record,
                    "word_detail": word
                }
                enriched_records.append(enriched_record)

        return jsonify({
            "success": True,
            "data": enriched_records,
            "count": len(enriched_records),
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
