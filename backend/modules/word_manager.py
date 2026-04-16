import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from backend.modules.dictionary_manager import DictionaryManager


class WordManager:
    """Manage word storage in backend/data/words.json."""

    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = data_dir
        self.words_file = os.path.join(data_dir, "words.json")
        self._ensure_data_files()

    def _ensure_data_files(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.words_file):
            self._create_default_words_file()

    def _create_default_words_file(self):
        default_data = {
            "metadata": {
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "total_words": 0,
                "last_sync": datetime.now().isoformat(),
            },
            "words": [],
        }
        self._write_json(self.words_file, default_data)

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

    def _normalize_word_text(self, word: str) -> str:
        return (word or "").strip().lower()

    def add_word(self, word_data: Dict) -> Dict:
        words_data = self._read_json(self.words_file)

        word_id = f"word_{uuid.uuid4().hex[:8]}"
        new_word = {
            "id": word_id,
            "word": word_data.get("word"),
            "phonetic": word_data.get("phonetic", ""),
            "translations": word_data.get("translations", []),
            "examples": word_data.get("examples", []),
            "added_date": datetime.now().isoformat().split("T")[0],
        }

        words_data.setdefault("words", []).append(new_word)
        words_data.setdefault("metadata", {})
        words_data["metadata"]["total_words"] = len(words_data["words"])
        words_data["metadata"]["last_sync"] = datetime.now().isoformat()

        self._write_json(self.words_file, words_data)

        return {
            "success": True,
            "word_id": word_id,
            "word": new_word,
        }

    def get_all_words(self) -> List[Dict]:
        words_data = self._read_json(self.words_file)
        return words_data.get("words", [])

    def get_word_by_id(self, word_id: str) -> Optional[Dict]:
        for word in self.get_all_words():
            if word.get("id") == word_id:
                return word
        return None

    def get_word_by_text(self, word_text: str) -> Optional[Dict]:
        normalized = self._normalize_word_text(word_text)
        if not normalized:
            return None

        for word in self.get_all_words():
            if self._normalize_word_text(word.get("word")) == normalized:
                return word
        return None

    def update_word(self, word_id: str, word_data: Dict) -> bool:
        words_data = self._read_json(self.words_file)

        for word in words_data.get("words", []):
            if word.get("id") != word_id:
                continue

            word["phonetic"] = word_data.get("phonetic", word.get("phonetic", ""))
            word["translations"] = word_data.get("translations", word.get("translations", []))
            word["examples"] = word_data.get("examples", word.get("examples", []))
            words_data["metadata"]["last_sync"] = datetime.now().isoformat()
            self._write_json(self.words_file, words_data)
            return True

        return False

    def merge_word_details(self, existing_word: Dict, new_word_data: Dict) -> bool:
        words_data = self._read_json(self.words_file)

        for word in words_data.get("words", []):
            if word.get("id") != existing_word.get("id"):
                continue

            if not word.get("phonetic") and new_word_data.get("phonetic"):
                word["phonetic"] = new_word_data["phonetic"]

            if not word.get("translations") and new_word_data.get("translations"):
                word["translations"] = new_word_data["translations"]

            if not word.get("examples") and new_word_data.get("examples"):
                word["examples"] = new_word_data["examples"]

            words_data["metadata"]["last_sync"] = datetime.now().isoformat()
            self._write_json(self.words_file, words_data)
            return True

        return False

    def delete_word(self, word_id: str) -> bool:
        words_data = self._read_json(self.words_file)
        original_count = len(words_data.get("words", []))
        words_data["words"] = [w for w in words_data.get("words", []) if w.get("id") != word_id]

        if len(words_data["words"]) < original_count:
            words_data["metadata"]["total_words"] = len(words_data["words"])
            words_data["metadata"]["last_sync"] = datetime.now().isoformat()
            self._write_json(self.words_file, words_data)
            return True

        return False

    def batch_import_words(self, words_list: List[Dict]) -> Dict:
        import_count = 0
        errors = []

        for word_data in words_list:
            try:
                existing_word = self.get_word_by_text(word_data.get("word", ""))
                if existing_word:
                    self.merge_word_details(existing_word, DictionaryManager.enrich_word_data(word_data))
                    continue

                enriched_word_data = DictionaryManager.enrich_word_data(word_data)
                self.add_word(enriched_word_data)
                import_count += 1
            except Exception as e:
                errors.append({"word": word_data.get("word"), "error": str(e)})

        return {
            "success": import_count > 0 or not errors,
            "imported_count": import_count,
            "total_count": len(words_list),
            "errors": errors,
        }

    def get_statistics(self) -> Dict:
        words_data = self._read_json(self.words_file)
        metadata = words_data.get("metadata", {})
        words = words_data.get("words", [])

        return {
            "total_words": len(words),
            "created_date": metadata.get("created_date"),
            "last_sync": metadata.get("last_sync"),
        }
