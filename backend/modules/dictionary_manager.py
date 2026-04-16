from typing import Dict, List, Optional

import requests


class DictionaryManager:
    """Fetch dictionary data from Free Dictionary API and normalize it."""

    API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    TIMEOUT = 10

    @staticmethod
    def lookup_word(word: str) -> Optional[Dict]:
        if not word:
            return None

        url = DictionaryManager.API_URL.format(word=word.strip())
        try:
            response = requests.get(url, timeout=DictionaryManager.TIMEOUT)
            if response.status_code != 200:
                return None

            payload = response.json()
            if not isinstance(payload, list) or not payload:
                return None

            return DictionaryManager._normalize_entry(payload[0])
        except Exception:
            return None

    @staticmethod
    def enrich_word_data(word_data: Dict) -> Dict:
        enriched = dict(word_data)
        lookup = DictionaryManager.lookup_word(enriched.get("word", ""))

        if not lookup:
            return enriched

        if not enriched.get("phonetic") and lookup.get("phonetic"):
            enriched["phonetic"] = lookup["phonetic"]

        if not enriched.get("translations") and lookup.get("translations"):
            enriched["translations"] = lookup["translations"]

        existing_examples = enriched.get("examples") or []
        if not existing_examples and lookup.get("examples"):
            enriched["examples"] = lookup["examples"]

        return enriched

    @staticmethod
    def _normalize_entry(entry: Dict) -> Dict:
        phonetic = DictionaryManager._extract_phonetic(entry)
        translations = DictionaryManager._extract_translations(entry)
        examples = DictionaryManager._extract_examples(entry)

        return {
            "phonetic": phonetic,
            "translations": translations,
            "examples": examples,
        }

    @staticmethod
    def _extract_phonetic(entry: Dict) -> str:
        phonetic = entry.get("phonetic")
        if phonetic:
            return phonetic

        for phonetic_item in entry.get("phonetics", []):
            text = phonetic_item.get("text")
            if text:
                return text

        return ""

    @staticmethod
    def _extract_translations(entry: Dict) -> List[Dict]:
        translations: List[Dict] = []

        for meaning in entry.get("meanings", []):
            part_of_speech = meaning.get("partOfSpeech", "other")
            for definition in meaning.get("definitions", []):
                text = definition.get("definition")
                if text:
                    translations.append({
                        "meaning": text,
                        "part_of_speech": part_of_speech,
                    })

                if len(translations) >= 5:
                    return translations

        return translations

    @staticmethod
    def _extract_examples(entry: Dict) -> List[Dict]:
        examples: List[Dict] = []

        for meaning in entry.get("meanings", []):
            domain = meaning.get("partOfSpeech", "General")
            for definition in meaning.get("definitions", []):
                sentence = definition.get("example")
                if sentence:
                    examples.append({
                        "sentence": sentence,
                        "translation": "",
                        "domain": domain,
                    })

                if len(examples) >= 3:
                    return examples

        return examples
