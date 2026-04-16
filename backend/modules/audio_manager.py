import urllib.parse
from typing import Dict, Optional

import requests


class AudioManager:
    """Manage pronunciation URLs, fallback phonetics, and connectivity checks."""

    GOOGLE_TTS_URL = "https://translate.google.com/translate_tts"

    _PHONETIC_MAP = {
        "algorithm": "/ˈælɡərɪðəm/",
        "cache": "/kæʃ/",
        "database": "/ˈdeɪtəbeɪs/",
        "debug": "/diːˈbʌɡ/",
        "function": "/ˈfʌŋkʃən/",
        "hash": "/hæʃ/",
        "integer": "/ˈɪntɪdʒər/",
        "loop": "/luːp/",
        "memory": "/ˈmeməri/",
        "network": "/ˈnetwɜːrk/",
        "object": "/ˈɒbdʒekt/",
        "process": "/ˈprəʊses/",
        "query": "/ˈkwɪəri/",
        "recursion": "/rɪˈkɜːrʒən/",
        "server": "/ˈsɜːrvər/",
        "thread": "/θred/",
        "variable": "/ˈveriəbəl/",
        "array": "/əˈreɪ/",
        "boolean": "/ˈbuːliən/",
        "circuit": "/ˈsɜːrkɪt/",
        "compile": "/kəmˈpaɪl/",
        "current": "/ˈkɜːrənt/",
        "data": "/ˈdeɪtə/",
        "device": "/dɪˈvaɪs/",
        "digital": "/ˈdɪdʒɪtəl/",
        "electric": "/ɪˈlektrɪk/",
        "electrode": "/ɪˈlektrəʊd/",
        "element": "/ˈelɪmənt/",
        "equipment": "/ɪˈkwɪpmənt/",
        "error": "/ˈerər/",
        "file": "/faɪl/",
        "filter": "/ˈfɪltər/",
        "hardware": "/ˈhɑːrdwer/",
        "import": "/ɪmˈpɔːrt/",
        "initialize": "/ɪˈnɪʃəlaɪz/",
        "input": "/ˈɪnpʊt/",
        "instruction": "/ɪnˈstrʌkʃən/",
        "interface": "/ˈɪntərfeɪs/",
        "library": "/ˈlaɪbreri/",
        "logic": "/ˈlɒdʒɪk/",
        "module": "/ˈmɒdjuːl/",
        "output": "/ˈaʊtpʊt/",
        "parameter": "/pəˈræmɪtər/",
        "pixel": "/ˈpɪksəl/",
        "port": "/pɔːrt/",
        "power": "/ˈpaʊər/",
        "protocol": "/ˈprəʊtəkɒl/",
        "register": "/ˈredʒɪstər/",
        "resistance": "/rɪˈzɪstəns/",
        "routine": "/ruːˈtiːn/",
        "script": "/skrɪpt/",
        "socket": "/ˈsɒkɪt/",
        "software": "/ˈsɒftwer/",
        "source": "/sɔːrs/",
        "storage": "/ˈstɔːrɪdʒ/",
        "string": "/strɪŋ/",
        "structure": "/ˈstrʌktʃər/",
        "system": "/ˈsɪstəm/",
        "terminal": "/ˈtɜːrmɪnəl/",
        "token": "/ˈtəʊkən/",
        "transmission": "/trænzˈmɪʃən/",
        "voltage": "/ˈvəʊltɪdʒ/",
        "wire": "/waɪər/",
    }

    @staticmethod
    def get_audio_url(word: str, language: str = "en") -> str:
        params = {
            "client": "gtx",
            "q": word,
            "tl": language,
        }
        return f"{AudioManager.GOOGLE_TTS_URL}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def _extract_phonetic_from_google(word: str) -> Optional[str]:
        return AudioManager._PHONETIC_MAP.get(word.lower())

    @staticmethod
    def get_phonetic_and_audio(word: str) -> Dict[str, Optional[str]]:
        phonetic = AudioManager._extract_phonetic_from_google(word) or ""
        return {
            "word": word,
            "phonetic": phonetic,
            "audio_url": AudioManager.get_audio_url(word, "en"),
            "audio_url_uk": AudioManager.get_audio_url(word, "en"),
            "success": True,
        }

    @staticmethod
    def validate_audio_url(audio_url: str, timeout: int = 5) -> bool:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://translate.google.com/",
        }
        try:
            response = requests.get(
                audio_url,
                timeout=timeout,
                allow_redirects=True,
                stream=True,
                headers=headers,
            )
            content_type = response.headers.get("Content-Type", "")
            is_valid = response.status_code == 200 and "audio" in content_type.lower()
            response.close()
            return is_valid
        except Exception:
            return False

    @staticmethod
    def format_phonetic_display(phonetic: str) -> str:
        if not phonetic:
            return ""
        if not phonetic.startswith("/"):
            phonetic = "/" + phonetic
        if not phonetic.endswith("/"):
            phonetic = phonetic + "/"
        return phonetic

    @staticmethod
    def get_pronunciation_info(word: str) -> Dict[str, str]:
        phonetic = AudioManager._extract_phonetic_from_google(word) or ""
        return {
            "word": word,
            "phonetic_us": phonetic,
            "phonetic_uk": phonetic,
            "audio_url_us": AudioManager.get_audio_url(word, "en"),
            "audio_url_uk": AudioManager.get_audio_url(word, "en"),
            "description": "US pronunciation",
        }

    @staticmethod
    def verify_google_tts(word: str = "hello", timeout: int = 8) -> Dict[str, object]:
        audio_url = AudioManager.get_audio_url(word, "en")
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://translate.google.com/",
        }
        try:
            response = requests.get(
                audio_url,
                headers=headers,
                timeout=timeout,
                stream=True,
                allow_redirects=True,
            )
            content_type = response.headers.get("Content-Type", "")
            reachable = response.status_code == 200 and "audio" in content_type.lower()
            response.close()
            return {
                "reachable": reachable,
                "status_code": response.status_code,
                "content_type": content_type,
                "audio_url": audio_url,
                "word": word,
                "message": "reachable" if reachable else "unexpected response",
            }
        except Exception as exc:
            return {
                "reachable": False,
                "status_code": None,
                "content_type": "",
                "audio_url": audio_url,
                "word": word,
                "message": str(exc),
            }
