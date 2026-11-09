"""Application logic, independent of any web framework (so it is easy to test)."""

from __future__ import annotations

import re
from collections import OrderedDict

from .config import Settings
from .extract import extract_profile
from .fields import clean_profile, clean_value, public_meta
from .llm import NullLLM, make_llm
from .retrieval import VectorIndex, build_index
from .rules import evaluate_all, load_documents, load_schemes, next_questions, scheme_by_id

DISCLAIMER = {
    "en": "This is guidance, not a final decision. Please confirm on the official website or at your nearest Common Service Centre before applying.",
    "hi": "यह केवल मार्गदर्शन है, अंतिम निर्णय नहीं। आवेदन से पहले कृपया आधिकारिक वेबसाइट या नज़दीकी कॉमन सर्विस सेंटर पर पुष्टि करें।",
    "kn": "ಇದು ಕೇವಲ ಮಾರ್ಗದರ್ಶನ, ಅಂತಿಮ ನಿರ್ಧಾರವಲ್ಲ. ಅರ್ಜಿ ಹಾಕುವ ಮೊದಲು ದಯವಿಟ್ಟು ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್ ಅಥವಾ ಹತ್ತಿರದ ಕಾಮನ್ ಸರ್ವಿಸ್ ಸೆಂಟರ್‌ನಲ್ಲಿ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.",
}


def detect_lang(text: str) -> str:
    """Guess en/hi/kn from the script of the text."""
    kannada = len(re.findall(r"[ಀ-೿]", text))
    hindi = len(re.findall(r"[ऀ-ॿ]", text))
    if kannada > hindi and kannada > 0:
        return "kn"
    if hindi > 0:
        return "hi"
    return "en"


class _Cache:
    """Tiny LRU so repeated calls with the same text do not repeat paid LLM calls."""

    def __init__(self, size: int = 256):
        self.size, self.data = size, OrderedDict()

    def get(self, key):
        if key in self.data:
            self.data.move_to_end(key)
            return self.data[key]
        return None

    def put(self, key, value):
        self.data[key] = value
        self.data.move_to_end(key)
        while len(self.data) > self.size:
            self.data.popitem(last=False)


class SchemeService:
    def __init__(self, settings: Settings | None = None, llm=None, index: VectorIndex | None = None):
        self.settings = settings or Settings()
        self.llm = llm if llm is not None else make_llm(self.settings.llm_provider, self.settings.anthropic_model)
        self.index = index or build_index(self.settings.embedding_backend, self.settings.embedding_model, self.settings.min_relevant_score)
        self._llm_cache = _Cache()

    # ---- info ---------------------------------------------------------------------------

    def health(self, transcription_available: bool = False) -> dict:
        schemes = load_schemes()
        verified = sum(1 for s in schemes if s.get("last_verified"))
        return {
            "status": "ok",
            "llm": self.llm.name if self.llm.available else None,
            "transcription": transcription_available,
            "embedding": self.index.embedder.name,
            "passages": len(self.index.passages),
            "schemes": len(schemes),
            "schemes_verified": verified,
        }

    def meta(self) -> dict:
        return public_meta()

    # ---- profile building ------------------------------------------------------------------

    def build_profile(self, text: str, overrides: dict | None = None) -> tuple[dict, dict, list[str], str | None]:
        """Returns (profile, field_sources, warnings, llm_error).

        Precedence: rules < LLM < user edits. Each field remembers where it came from.
        """
        profile: dict = {}
        sources: dict[str, str] = {}
        warnings: list[str] = []
        llm_error = None

        if text.strip():
            rule_result = extract_profile(text)
            profile.update(rule_result["profile"])
            sources.update({k: "rules" for k in rule_result["profile"]})
            warnings.extend(rule_result["warnings"])

            if self.llm.available:
                cached = self._llm_cache.get(text)
                if cached is None:
                    try:
                        cached = clean_profile(self.llm.extract_profile(text))
                        self._llm_cache.put(text, cached)
                    except Exception as exc:  # never let a model hiccup break the request
                        llm_error = exc.__class__.__name__
                        cached = {}
                for k, v in cached.items():
                    profile[k] = v
                    sources[k] = "llm"
                    if k == "annual_income" and "income_period_unclear" in warnings:
                        warnings.remove("income_period_unclear")

        for field, value in (overrides or {}).items():
            if value is None:  # user cleared the field
                profile.pop(field, None)
                sources.pop(field, None)
                continue
            cleaned = clean_value(field, value)
            if cleaned is not None:
                profile[field] = cleaned
                sources[field] = "user"
        return profile, sources, warnings, llm_error

    # ---- main entry points ----------------------------------------------------------------------

    def analyze(self, text: str = "", overrides: dict | None = None, lang: str | None = None) -> dict:
        text = (text or "")[: self.settings.max_text_chars]
        text_lang = detect_lang(text)  # the language the person SPOKE: used to rank schemes by relevance
        lang = lang if lang in ("en", "hi", "kn") else text_lang  # the language to SHOW citations and the disclaimer in

        profile, sources, warnings, llm_error = self.build_profile(text, overrides)
        evaluations = evaluate_all(profile)
        relevance = self.index.scheme_scores(text, text_lang) if text.strip() else {}
        documents = load_documents()

        results = []
        for ev in evaluations:
            scheme = scheme_by_id(ev["id"])
            citations = []
            if text.strip() and ev["status"] != "not_eligible":
                hits = self.index.search(text, k=2, lang=lang, scheme_ids={scheme["id"]})
                citations = [p.public(score) for p, score in hits]
            if not citations and ev["status"] != "not_eligible":
                # Always give at least the official eligibility passage so the claim is checkable.
                fallback = self.index.search(scheme["name"][lang], k=1, lang=lang, scheme_ids={scheme["id"]})
                citations = [p.public(s) for p, s in fallback]
            results.append(
                {
                    **ev,
                    "level": scheme["level"],
                    "category": scheme["category"],
                    "name": scheme["name"],
                    "summary": scheme["summary"],
                    "benefit": scheme["benefit"],
                    "how_to_apply": scheme["how_to_apply"],
                    "apply_url": scheme["apply_url"],
                    "source_url": scheme["source_url"],
                    "documents": [{"id": d, "text": documents[d]} for d in scheme["documents"]],
                    "relevance": round(relevance.get(scheme["id"], 0.0), 4),
                    "last_verified": scheme.get("last_verified"),
                    "citations": citations,
                }
            )
        # Group order (eligible, likely, not_eligible) is already set; within a group, most relevant first.
        group = {"eligible": 0, "likely": 1, "not_eligible": 2}
        results.sort(key=lambda r: (group[r["status"]], -r["relevance"]))

        counts = {s: sum(1 for r in results if r["status"] == s) for s in ("eligible", "likely", "not_eligible")}
        return {
            "lang": lang,
            "profile": profile,
            "field_sources": sources,
            "warnings": warnings,
            "next_questions": next_questions(evaluations),
            "counts": counts,
            "results": results,
            "llm_used": bool(self.llm.available and not llm_error and text.strip()),
            "llm_error": llm_error,
            "disclaimer": DISCLAIMER[lang],
            "data_verified": all(s.get("last_verified") for s in load_schemes()),
        }

    def ask(self, question: str, lang: str | None = None) -> dict:
        question = (question or "").strip()[: self.settings.max_text_chars]
        # Retrieval works within one language, so search in the language the question was WRITTEN in.
        # `lang` (the interface language) only decides which language an LLM answer is written in.
        search_lang = detect_lang(question)
        lang = lang if lang in ("en", "hi", "kn") else search_lang
        hits = self.index.search(question, k=4, lang=search_lang)
        passages = [p.public(s) for p, s in hits]  # the index already drops anything below its relevance floor
        top = hits[0][1] if hits else 0.0
        confidence = "none" if not hits else ("high" if top >= self.index.confident_score else "low")

        answer, llm_error = None, None
        if passages and self.llm.available:
            try:
                answer = self.llm.answer(question, passages, lang)
            except Exception as exc:
                llm_error = exc.__class__.__name__
        return {
            "lang": lang,
            "answer": answer,  # None when no LLM: the UI then shows the passages themselves
            "grounded": bool(passages),
            "confidence": confidence,  # "none" | "low" (weak match: warn the user) | "high"
            "passages": passages,
            "llm_error": llm_error,
            "disclaimer": DISCLAIMER[lang],
        }
