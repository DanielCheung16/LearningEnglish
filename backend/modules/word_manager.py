import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid

class WordManager:
    """管理单词数据库，处理JSON文件的读写"""

    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = data_dir
        self.words_file = os.path.join(data_dir, "words.json")
        self._ensure_data_files()

    def _ensure_data_files(self):
        """确保数据文件夹和初始文件存在"""
        os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self.words_file):
            self._create_default_words_file()

    def _create_default_words_file(self):
        """创建默认的words.json文件"""
        default_data = {
            "metadata": {
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "total_words": 0,
                "last_sync": datetime.now().isoformat()
            },
            "words": []
        }
        self._write_json(self.words_file, default_data)

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

    def add_word(self, word_data: Dict) -> Dict:
        """
        添加新单词

        参数:
            word_data: {
                "word": "algorithm",
                "phonetic": "/ˈælɡərɪðəm/",
                "translations": [{"meaning": "算法", "part_of_speech": "noun"}],
                "examples": [{
                    "sentence": "The sorting algorithm...",
                    "domain": "Computer Science",
                    "translation": "排序算法..."
                }]
            }

        返回:
            包含新单词ID的数据
        """
        words_data = self._read_json(self.words_file)

        # 生成唯一ID
        word_id = f"word_{uuid.uuid4().hex[:8]}"

        new_word = {
            "id": word_id,
            "word": word_data.get("word"),
            "phonetic": word_data.get("phonetic", ""),
            "translations": word_data.get("translations", []),
            "examples": word_data.get("examples", []),
            "added_date": datetime.now().isoformat().split('T')[0]
        }

        words_data["words"].append(new_word)
        words_data["metadata"]["total_words"] = len(words_data["words"])
        words_data["metadata"]["last_sync"] = datetime.now().isoformat()

        self._write_json(self.words_file, words_data)

        return {
            "success": True,
            "word_id": word_id,
            "word": new_word
        }

    def get_all_words(self) -> List[Dict]:
        """获取所有单词"""
        words_data = self._read_json(self.words_file)
        return words_data.get("words", [])

    def get_word_by_id(self, word_id: str) -> Optional[Dict]:
        """通过ID获取单个单词"""
        words_data = self._read_json(self.words_file)
        for word in words_data.get("words", []):
            if word["id"] == word_id:
                return word
        return None

    def update_word(self, word_id: str, word_data: Dict) -> bool:
        """更新单词信息"""
        words_data = self._read_json(self.words_file)

        for i, word in enumerate(words_data["words"]):
            if word["id"] == word_id:
                # 更新允许修改的字段
                word["phonetic"] = word_data.get("phonetic", word["phonetic"])
                word["translations"] = word_data.get("translations", word["translations"])
                word["examples"] = word_data.get("examples", word["examples"])

                words_data["metadata"]["last_sync"] = datetime.now().isoformat()
                self._write_json(self.words_file, words_data)
                return True

        return False

    def delete_word(self, word_id: str) -> bool:
        """删除单词"""
        words_data = self._read_json(self.words_file)

        original_count = len(words_data["words"])
        words_data["words"] = [w for w in words_data["words"] if w["id"] != word_id]

        if len(words_data["words"]) < original_count:
            words_data["metadata"]["total_words"] = len(words_data["words"])
            words_data["metadata"]["last_sync"] = datetime.now().isoformat()
            self._write_json(self.words_file, words_data)
            return True

        return False

    def batch_import_words(self, words_list: List[Dict]) -> Dict:
        """批量导入单词"""
        import_count = 0
        errors = []

        for word_data in words_list:
            try:
                self.add_word(word_data)
                import_count += 1
            except Exception as e:
                errors.append({"word": word_data.get("word"), "error": str(e)})

        return {
            "success": import_count > 0,
            "imported_count": import_count,
            "total_count": len(words_list),
            "errors": errors
        }

    def get_statistics(self) -> Dict:
        """获取单词统计信息"""
        words_data = self._read_json(self.words_file)
        words = words_data.get("words", [])

        return {
            "total_words": len(words),
            "created_date": words_data["metadata"]["created_date"],
            "last_sync": words_data["metadata"]["last_sync"]
        }
