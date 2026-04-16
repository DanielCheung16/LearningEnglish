from flask import Blueprint, request, jsonify
from backend.modules.word_manager import WordManager
from backend.modules.review_manager import ReviewManager
from backend.modules.audio_manager import AudioManager

word_bp = Blueprint('words', __name__, url_prefix='/api/words')

# 初始化管理器
word_manager = WordManager()
review_manager = ReviewManager()


@word_bp.route('', methods=['POST'])
def add_word():
    """
    添加新单词

    请求体:
    {
        "word": "algorithm",
        "phonetic": "/ˈælɡərɪðəm/",
        "translations": [
            {"meaning": "算法", "part_of_speech": "noun"}
        ],
        "examples": [
            {
                "sentence": "The sorting algorithm has O(n log n) complexity.",
                "domain": "Computer Science",
                "translation": "排序算法的时间复杂度为 O(n log n)。"
            }
        ]
    }
    """
    try:
        data = request.get_json()

        if not data.get("word"):
            return jsonify({
                "success": False,
                "error": "单词不能为空"
            }), 400

        # 获取音频信息
        audio_info = AudioManager.get_phonetic_and_audio(data["word"])
        if audio_info.get("phonetic"):
            data["phonetic"] = audio_info["phonetic"]

        # 添加单词
        result = word_manager.add_word(data)

        if result.get("success"):
            word_id = result["word_id"]
            # 初始化复习记录
            review_manager.initialize_review_for_word(word_id, data["word"])

            return jsonify({
                "success": True,
                "message": "单词已添加",
                "word_id": word_id,
                "word": result["word"]
            }), 201
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@word_bp.route('', methods=['GET'])
def get_all_words():
    """获取所有单词"""
    try:
        words = word_manager.get_all_words()
        stats = word_manager.get_statistics()

        return jsonify({
            "success": True,
            "data": words,
            "statistics": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@word_bp.route('/<word_id>', methods=['GET'])
def get_word(word_id):
    """获取特定单词"""
    try:
        word = word_manager.get_word_by_id(word_id)

        if word:
            # 获取复习信息
            review_record = review_manager.get_review_history(word_id)

            return jsonify({
                "success": True,
                "word": word,
                "review_info": review_record
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


@word_bp.route('/<word_id>', methods=['PUT'])
def update_word(word_id):
    """
    更新单词信息

    请求体（只支持更新以下字段）:
    {
        "phonetic": "/ˈælɡərɪðəm/",
        "translations": [...],
        "examples": [...]
    }
    """
    try:
        data = request.get_json()

        if word_manager.update_word(word_id, data):
            updated_word = word_manager.get_word_by_id(word_id)
            return jsonify({
                "success": True,
                "message": "单词已更新",
                "word": updated_word
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


@word_bp.route('/<word_id>', methods=['DELETE'])
def delete_word(word_id):
    """删除单词及其复习记录"""
    try:
        if word_manager.delete_word(word_id):
            review_manager.delete_review_record(word_id)
            return jsonify({
                "success": True,
                "message": "单词已删除"
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


@word_bp.route('/batch-import', methods=['POST'])
def batch_import():
    """
    批量导入单词

    请求体:
    {
        "words": [
            {
                "word": "algorithm",
                "phonetic": "/ˈælɡərɪðəm/",
                "translations": [...],
                "examples": [...]
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        words_list = data.get("words", [])

        if not words_list:
            return jsonify({
                "success": False,
                "error": "单词列表不能为空"
            }), 400

        result = word_manager.batch_import_words(words_list)

        # 为每个导入的单词初始化复习记录
        if result.get("success"):
            all_words = word_manager.get_all_words()
            for word in all_words[-result["imported_count"]:]:
                review_manager.initialize_review_for_word(word["id"], word["word"])

        return jsonify({
            "success": result.get("success"),
            "message": f"成功导入 {result['imported_count']} 个单词",
            "imported_count": result["imported_count"],
            "total_count": result["total_count"],
            "errors": result.get("errors", [])
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@word_bp.route('/search', methods=['GET'])
def search_words():
    """
    搜索单词

    查询参数:
        q: 搜索关键词
    """
    try:
        query = request.args.get('q', '').lower()

        if not query:
            return jsonify({
                "success": False,
                "error": "搜索关键词不能为空"
            }), 400

        all_words = word_manager.get_all_words()
        results = [
            word for word in all_words
            if query in word.get("word", "").lower() or
               any(query in str(t.get("meaning", "")).lower() for t in word.get("translations", []))
        ]

        return jsonify({
            "success": True,
            "data": results,
            "count": len(results)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@word_bp.route('/audio-info', methods=['POST'])
def get_audio_info():
    """
    获取单词的音频和音标信息

    请求体:
    {
        "word": "algorithm"
    }
    """
    try:
        data = request.get_json()
        word = data.get("word")

        if not word:
            return jsonify({
                "success": False,
                "error": "单词不能为空"
            }), 400

        audio_info = AudioManager.get_pronunciation_info(word)

        return jsonify({
            "success": True,
            "data": audio_info
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@word_bp.route('/audio-verify', methods=['POST'])
def verify_audio_connectivity():
    """Verify whether Google TTS is reachable."""
    try:
        data = request.get_json() or {}
        word = data.get("word", "hello")
        result = AudioManager.verify_google_tts(word)

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
