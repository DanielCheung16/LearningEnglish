from flask import Blueprint, jsonify, request

from backend.modules.audio_manager import AudioManager
from backend.modules.dictionary_manager import DictionaryManager
from backend.modules.review_manager import ReviewManager
from backend.modules.word_manager import WordManager

word_bp = Blueprint("words", __name__, url_prefix="/api/words")

word_manager = WordManager()
review_manager = ReviewManager()


@word_bp.route("", methods=["POST"])
def add_word():
    try:
        data = request.get_json() or {}

        if not data.get("word"):
            return jsonify({"success": False, "error": "Word cannot be empty"}), 400

        data = DictionaryManager.enrich_word_data(data)
        if not data.get("phonetic"):
            audio_info = AudioManager.get_phonetic_and_audio(data["word"])
            if audio_info.get("phonetic"):
                data["phonetic"] = audio_info["phonetic"]

        existing_word = word_manager.get_word_by_text(data["word"])
        if existing_word:
            word_manager.merge_word_details(existing_word, data)
            penalty_result = review_manager.penalize_duplicate_word(existing_word["id"])
            updated_word = word_manager.get_word_by_id(existing_word["id"]) or existing_word

            return jsonify({
                "success": True,
                "duplicate": True,
                "message": "Word already exists. Mastery has been lowered for review.",
                "word_id": existing_word["id"],
                "word": updated_word,
                "review_status": {
                    "next_review_date": penalty_result.get("next_review_date"),
                    "master_level": penalty_result.get("master_level"),
                    "status": penalty_result.get("status"),
                },
            }), 200

        result = word_manager.add_word(data)
        if result.get("success"):
            word_id = result["word_id"]
            review_record = review_manager.initialize_review_for_word(word_id, data["word"])
            return jsonify({
                "success": True,
                "message": "Word added successfully",
                "word_id": word_id,
                "word": result["word"],
                "review_status": {
                    "next_review_date": review_record.get("next_review_date"),
                    "master_level": review_record.get("master_level"),
                    "status": review_record.get("status"),
                },
            }), 201

        return jsonify(result), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("", methods=["GET"])
def get_all_words():
    try:
        words = word_manager.get_all_words()
        stats = word_manager.get_statistics()
        return jsonify({"success": True, "data": words, "statistics": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/<word_id>", methods=["GET"])
def get_word(word_id):
    try:
        word = word_manager.get_word_by_id(word_id)
        if not word:
            return jsonify({"success": False, "error": f"Word ID {word_id} does not exist"}), 404

        review_record = review_manager.get_review_history(word_id)
        return jsonify({"success": True, "word": word, "review_info": review_record})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/<word_id>", methods=["PUT"])
def update_word(word_id):
    try:
        data = request.get_json() or {}
        if word_manager.update_word(word_id, data):
            updated_word = word_manager.get_word_by_id(word_id)
            return jsonify({
                "success": True,
                "message": "Word updated successfully",
                "word": updated_word,
            })
        return jsonify({"success": False, "error": f"Word ID {word_id} does not exist"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/<word_id>", methods=["DELETE"])
def delete_word(word_id):
    try:
        if word_manager.delete_word(word_id):
            review_manager.delete_review_record(word_id)
            return jsonify({"success": True, "message": "Word deleted successfully"})
        return jsonify({"success": False, "error": f"Word ID {word_id} does not exist"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/batch-delete", methods=["POST"])
def batch_delete_words():
    try:
        data = request.get_json() or {}
        word_ids = data.get("word_ids", [])

        if not isinstance(word_ids, list) or not word_ids:
            return jsonify({"success": False, "error": "word_ids must be a non-empty list"}), 400

        result = word_manager.batch_delete_words(word_ids)
        if not result.get("success"):
            return jsonify({"success": False, "error": "No matching words were found"}), 404

        review_deleted_count = review_manager.delete_review_records(result.get("deleted_ids", []))
        return jsonify({
            "success": True,
            "message": f"Deleted {result['deleted_count']} words successfully",
            "deleted_count": result["deleted_count"],
            "review_deleted_count": review_deleted_count,
            "deleted_ids": result.get("deleted_ids", []),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/batch-import", methods=["POST"])
def batch_import():
    try:
        data = request.get_json() or {}
        words_list = data.get("words", [])
        if not words_list:
            return jsonify({"success": False, "error": "Word list cannot be empty"}), 400

        result = word_manager.batch_import_words(words_list)
        if result.get("success") and result.get("imported_count", 0) > 0:
            all_words = word_manager.get_all_words()
            for word in all_words[-result["imported_count"]:]:
                review_manager.initialize_review_for_word(word["id"], word["word"])

        return jsonify({
            "success": result.get("success"),
            "message": f"Imported {result['imported_count']} words successfully",
            "imported_count": result["imported_count"],
            "total_count": result["total_count"],
            "errors": result.get("errors", []),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/search", methods=["GET"])
def search_words():
    try:
        query = request.args.get("q", "").lower()
        if not query:
            return jsonify({"success": False, "error": "Search query cannot be empty"}), 400

        all_words = word_manager.get_all_words()
        results = [
            word for word in all_words
            if query in word.get("word", "").lower()
            or any(query in str(t.get("meaning", "")).lower() for t in word.get("translations", []))
        ]
        return jsonify({"success": True, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/audio-info", methods=["POST"])
def get_audio_info():
    try:
        data = request.get_json() or {}
        word = data.get("word")
        if not word:
            return jsonify({"success": False, "error": "Word cannot be empty"}), 400

        audio_info = AudioManager.get_pronunciation_info(word)
        return jsonify({"success": True, "data": audio_info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/audio-verify", methods=["POST"])
def verify_audio_connectivity():
    try:
        data = request.get_json() or {}
        word = data.get("word", "hello")
        result = AudioManager.verify_audio_source(word)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
