from flask import Blueprint, jsonify, request

from backend.modules.review_manager import ReviewManager
from backend.modules.word_manager import WordManager

review_bp = Blueprint("review", __name__, url_prefix="/api/review")

review_manager = ReviewManager()
word_manager = WordManager()


@review_bp.route("/today", methods=["GET"])
def get_today_review_list():
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        today_reviews = review_manager.get_today_review_list()
        enriched_reviews = []

        for review_record in today_reviews:
            word_id = review_record.get("word_id")
            word = word_manager.get_word_by_id(word_id)
            if word:
                if word.get("added_date") == today and review_record.get("review_count", 0) == 0:
                    continue
                enriched_reviews.append({**review_record, "word_detail": word})

        return jsonify({
            "success": True,
            "data": enriched_reviews,
            "count": len(enriched_reviews),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@review_bp.route("/today-new", methods=["GET"])
def get_today_new_words():
    try:
        today = request.args.get("date")
        if not today:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")

        new_word_reviews = []
        for word in word_manager.get_all_words():
            if word.get("added_date") != today:
                continue

            review_record = review_manager.get_review_history(word.get("id"))
            if not review_record:
                review_record = review_manager.initialize_review_for_word(word.get("id"), word.get("word", ""))

            if review_record.get("review_count", 0) == 0:
                new_word_reviews.append({**review_record, "word_detail": word})

        return jsonify({
            "success": True,
            "data": new_word_reviews,
            "count": len(new_word_reviews),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@review_bp.route("/submit", methods=["POST"])
def submit_review():
    try:
        data = request.get_json() or {}
        word_id = data.get("word_id")
        proficiency_level = data.get("proficiency_level", "familiar")

        if not word_id:
            return jsonify({"success": False, "error": "word_id cannot be empty"}), 400

        valid_levels = ["unfamiliar", "familiar", "practiced", "mastered"]
        if proficiency_level not in valid_levels:
            return jsonify({
                "success": False,
                "error": f"Invalid proficiency level. Expected one of: {', '.join(valid_levels)}",
            }), 400

        result = review_manager.submit_review(word_id, proficiency_level)
        if not result.get("success"):
            return jsonify(result), 404

        word = word_manager.get_word_by_id(word_id)
        return jsonify({
            "success": True,
            "message": "Review submitted successfully",
            "next_review_date": result.get("next_review_date"),
            "master_level": result.get("master_level"),
            "status": result.get("status"),
            "fsrs": result.get("fsrs"),
            "word": word,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@review_bp.route("/history/<word_id>", methods=["GET"])
def get_review_history(word_id):
    try:
        review_record = review_manager.get_review_history(word_id)
        if not review_record:
            return jsonify({"success": False, "error": f"Review history for {word_id} does not exist"}), 404

        word = word_manager.get_word_by_id(word_id)
        return jsonify({
            "success": True,
            "word": word,
            "review_history": review_record,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@review_bp.route("/stats", methods=["GET"])
def get_review_stats():
    try:
        stats = review_manager.get_review_stats()
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@review_bp.route("/overdue", methods=["GET"])
def get_overdue_reviews():
    try:
        overdue_reviews = review_manager.get_overdue_reviews()
        enriched_reviews = []

        for review_record in overdue_reviews:
            word_id = review_record.get("word_id")
            word = word_manager.get_word_by_id(word_id)
            if word:
                enriched_reviews.append({**review_record, "word_detail": word})

        return jsonify({
            "success": True,
            "data": enriched_reviews,
            "count": len(enriched_reviews),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@review_bp.route("/reset/<word_id>", methods=["POST"])
def reset_word_review(word_id):
    try:
        if not review_manager.reset_word_review(word_id):
            return jsonify({"success": False, "error": f"Word ID {word_id} does not exist"}), 404

        review_record = review_manager.get_review_history(word_id)
        return jsonify({
            "success": True,
            "message": "Review progress reset successfully",
            "review_record": review_record,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@review_bp.route("/by-date", methods=["GET"])
def get_review_by_date():
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if not start_date or not end_date:
            return jsonify({"success": False, "error": "start_date and end_date cannot be empty"}), 400

        records = review_manager.get_review_by_date_range(start_date, end_date)
        enriched_records = []

        for review_record in records:
            word_id = review_record.get("word_id")
            word = word_manager.get_word_by_id(word_id)
            if word:
                enriched_records.append({**review_record, "word_detail": word})

        return jsonify({
            "success": True,
            "data": enriched_records,
            "count": len(enriched_records),
            "date_range": {"start": start_date, "end": end_date},
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
