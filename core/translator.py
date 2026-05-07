"""Translation engines with multi-engine support."""

import json
import sys
import time as _time
import requests
from typing import Protocol

from .terminology import TerminologyDB


class TranslationEngine(Protocol):
    """Protocol for translation engines."""
    def translate(self, text: str, source_lang: str, target_lang: str) -> str: ...


class GoogleTranslator:
    """Free Google Translate via unofficial API."""

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})

    def translate(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": source_lang,
            "tl": target_lang,
            "dt": "t",
            "q": text,
        }
        print(f"[Google] sl={source_lang} tl={target_lang} len={len(text)}", file=sys.stderr)
        _start = _time.time()
        try:
            resp = self._session.get(url, params=params, timeout=30)
            elapsed = _time.time() - _start
            print(f"[Google] Status: {resp.status_code} in {elapsed:.1f}s", file=sys.stderr)
            resp.raise_for_status()
            data = resp.json()
            return "".join(seg[0] for seg in data[0] if seg[0])
        except Exception as e:
            elapsed = _time.time() - _start
            print(f"[Google] ERROR after {elapsed:.1f}s: {e}", file=sys.stderr)
            raise


class DeepLTranslator:
    """DeepL API translation."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2/translate"
        if not api_key.endswith(":fx"):
            self.base_url = "https://api.deepl.com/v2/translate"

    def translate(self, text: str, source_lang: str = "EN", target_lang: str = "ZH") -> str:
        resp = requests.post(
            self.base_url,
            data={
                "auth_key": self.api_key,
                "text": text,
                "source_lang": source_lang.upper(),
                "target_lang": target_lang.upper(),
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["translations"][0]["text"]


class LLMTranslator:
    """LLM-based translation (Claude/GPT compatible API)."""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com",
                 model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def translate(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
        system_prompt = (
            "You are a professional translator specializing in electronic engineering "
            "and semiconductor datasheets. Translate the following text accurately, "
            "preserving technical terms, numbers, units, and formatting. "
            "Only output the translation, nothing else."
        )
        resp = requests.post(
            f"{self.base_url}/v1/messages",
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": f"Translate from {source_lang} to {target_lang}:\n{text}"}],
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


class TranslationManager:
    """Manage translation engines and coordinate translation with terminology."""

    def __init__(self, config: dict, terminology: TerminologyDB):
        self.config = config
        self.terminology = terminology
        self._engines: dict[str, TranslationEngine] = {}
        self._init_engines()

    def _init_engines(self):
        """Initialize available translation engines."""
        self._engines["google"] = GoogleTranslator()
        if self.config.get("deepl_api_key"):
            self._engines["deepl"] = DeepLTranslator(self.config["deepl_api_key"])
        if self.config.get("llm_api_key"):
            self._engines["llm"] = LLMTranslator(
                api_key=self.config["llm_api_key"],
                base_url=self.config.get("llm_base_url", "https://api.anthropic.com"),
                model=self.config.get("llm_model", "claude-sonnet-4-20250514"),
            )

    def reload_engines(self):
        """Reload engines after config change."""
        self._init_engines()

    def get_available_engines(self) -> list[str]:
        """Return list of available engine names."""
        return list(self._engines.keys())

    def translate(self, text: str, engine: str | None = None,
                  source_lang: str | None = None,
                  target_lang: str | None = None) -> dict:
        """Translate text with terminology post-processing.

        Args:
            text: text to translate
            engine: engine name (google/deepl/llm), None = use config
            source_lang: source language code, None = use config
            target_lang: target language code, None = use config

        Returns dict with:
            - original: original text
            - translated: translated text
            - engine: engine used
            - terms_applied: list of (en, zh) term pairs found
        """
        if not text.strip():
            return {"original": text, "translated": "", "engine": "none", "terms_applied": []}

        src = source_lang or self.config.get("source_lang", "en")
        tgt = target_lang or self.config.get("target_lang", "zh")

        # Build fallback chain: primary engine first, then remaining available engines
        primary = engine or self.config.get("translation_engine", "google")
        fallback_chain = [primary] + [e for e in self._engines if e != primary]

        last_error = None
        for engine_name in fallback_chain:
            if engine_name not in self._engines:
                continue
            try:
                translated = self._engines[engine_name].translate(text, src, tgt)
                _, terms_applied = self.terminology.apply_terms(text)
                return {
                    "original": text,
                    "translated": translated,
                    "engine": engine_name,
                    "terms_applied": terms_applied,
                }
            except Exception as e:
                last_error = e
                import sys
                print(f"[Fallback] {engine_name} failed: {e}, trying next...", file=sys.stderr)
                continue

        raise last_error or RuntimeError("No translation engine available")
