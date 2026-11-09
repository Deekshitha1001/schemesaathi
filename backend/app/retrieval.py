"""Retrieval over scheme passages, with citations.

Pipeline:  scheme records (+ optional ingested official text)  ->  passages
           passages -> embeddings -> vector index -> top-k passages for a query.

Every passage carries the scheme id, a section name and the official source URL,
so every answer can show *where* a statement came from.

Embedding backends (pick with EMBEDDING_BACKEND):
  tfidf (default)        character n-gram TF-IDF. Runs offline with scikit-learn only.
                         Works within a language (Hindi query -> Hindi passages).
  sentence-transformers  multilingual dense embeddings (default model:
                         intfloat/multilingual-e5-small, 100 languages incl. Kannada).
                         Needs `pip install sentence-transformers` and a model download.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .rules import DATA_DIR, load_documents, load_schemes

EXTRA_PASSAGES = DATA_DIR / "passages_extra.jsonl"  # written by scripts/ingest_documents.py


@dataclass
class Passage:
    id: str
    scheme_id: str
    section: str
    lang: str
    text: str
    source_url: str
    origin: str = "seed"  # "seed" = our structured summary, "ingested" = text from a scraped/official document
    meta: dict = field(default_factory=dict)

    def public(self, score: float | None = None) -> dict:
        out = {
            "id": self.id,
            "scheme_id": self.scheme_id,
            "section": self.section,
            "lang": self.lang,
            "text": self.text,
            "source_url": self.source_url,
            "origin": self.origin,
        }
        if score is not None:
            out["score"] = round(float(score), 4)
        return out


def build_passages(include_extra: bool = True) -> list[Passage]:
    """One passage per (scheme, section, language) from the structured data."""
    docs = load_documents()
    passages: list[Passage] = []
    for scheme in load_schemes():
        for lang in ("en", "hi", "kn"):
            name = scheme["name"][lang]
            eligibility = "; ".join(c["text"][lang] for c in scheme["criteria"])
            documents = ", ".join(docs[d][lang] for d in scheme["documents"])
            sections = {
                "overview": f"{name}. {scheme['summary'][lang]}",
                "benefit": f"{name}. {scheme['benefit'][lang]}",
                "eligibility": f"{name}. {eligibility}",
                "apply": f"{name}. {scheme['how_to_apply'][lang]} {documents}",
            }
            for section, text in sections.items():
                passages.append(
                    Passage(
                        id=f"{scheme['id']}:{section}:{lang}",
                        scheme_id=scheme["id"],
                        section=section,
                        lang=lang,
                        text=text,
                        source_url=scheme["source_url"],
                    )
                )
    if include_extra and EXTRA_PASSAGES.exists():
        with open(EXTRA_PASSAGES, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    row = json.loads(line)
                    passages.append(Passage(origin="ingested", **row))
    return passages


# --- embedders ------------------------------------------------------------------------


# Words that carry no topic. Without this, "what is the weather in paris" looks similar to
# any passage that happens to contain "what", "the" or "is" (character n-grams love them).
_STOPWORDS_EN = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "am", "do", "does", "did", "have", "has", "had",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "its", "they", "their", "this", "that", "these",
    "those", "what", "which", "who", "whom", "whose", "when", "where", "why", "how", "can", "could", "will", "would",
    "should", "shall", "may", "might", "must", "to", "of", "in", "on", "at", "for", "from", "by", "with", "about",
    "into", "and", "or", "but", "if", "then", "so", "as", "not", "no", "yes", "any", "some", "get", "got", "give",
    "gives", "need", "want", "tell", "please", "much", "many", "every", "each", "also", "than", "there", "here",
    "up", "out", "over", "after", "before", "me", "us", "best", "good",
}
_STOPWORDS_HI = {
    "है", "हैं", "था", "थी", "थे", "का", "की", "के", "को", "में", "से", "पर", "और", "या", "क्या", "कि", "यह", "वह",
    "ये", "वे", "कितना", "कितनी", "कितने", "कैसे", "कैसा", "कैसी", "मुझे", "मैं", "मेरा", "मेरी", "हम", "आप", "लिए",
    "भी", "तो", "ही", "नहीं", "एक", "कौन", "कब", "कहां", "कहाँ", "हो", "होता", "होती", "सकता", "सकती", "चाहिए",
    "बाद", "तक", "द्वारा", "जो", "सबसे", "अच्छा", "अच्छी", "कौनसा", "कौन", "सा", "सी", "बारे", "साल", "हर",
}
_STOPWORDS_KN = {
    "ಈ", "ಆ", "ಒಂದು", "ಮತ್ತು", "ಅಥವಾ", "ಏನು", "ಯಾವ", "ಯಾವುದು", "ಎಷ್ಟು", "ಹೇಗೆ", "ಹೇಗಿದೆ", "ಇದೆ", "ಇದೆಯೇ", "ಇಲ್ಲ",
    "ನನಗೆ", "ನಾನು", "ನೀವು", "ನಿಮಗೆ", "ಬೇಕು", "ಆಗಿದೆ", "ಇಂದು", "ಅದು", "ಇದು", "ಯಾರು", "ಯಾವಾಗ", "ಎಲ್ಲಿ", "ಸಿಗುತ್ತದೆ",
    "ಮಾಡುವುದು", "ಎಂದರೆ", "ಬಗ್ಗೆ", "ಅತ್ಯುತ್ತಮ",
}
STOPWORDS = _STOPWORDS_EN | _STOPWORDS_HI | _STOPWORDS_KN
_TOKEN = re.compile(r"[^\s.,;:!?()\[\]{}\"'/\\\-–—|•₹।]+")


def content_words(text: str) -> list[str]:
    """Lower-cased words minus stopwords and bare numbers (works for Latin, Devanagari and Kannada)."""
    words = []
    for w in _TOKEN.findall(text.lower()):
        if w in STOPWORDS or w.isdigit() or len(w) < 2:
            continue
        if w.endswith("s") and not w.endswith(("ss", "is", "us")) and len(w) > 4 and w.isascii():  # crude plural strip: "farmers" -> "farmer"
            w = w[:-1]
        words.append(w)
    return words


class TfidfEmbedder:
    """Hybrid lexical embedder: character n-grams (robust to Indic suffixes and spelling variants)
    blended with word-level TF-IDF over content words (what makes "weather" NOT match a scheme).

    cosine(q, p) = CHAR_WEIGHT * cos_char + (1 - CHAR_WEIGHT) * cos_word

    `gate()` tells the index which passages share at least one content word with the query.
    Every retrieval hit must pass that gate, which is what lets the app say "I don't know".
    """

    name = "tfidf"
    CHAR_WEIGHT = 0.5
    min_score = 0.10  # below this nothing is returned; override with MIN_RELEVANT_SCORE
    confident_score = 0.30  # below this the UI warns "this may not answer your question"
    uses_gate = True

    def __init__(self, max_features: int = 8000):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._char = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, max_features=max_features, lowercase=True)
        self._word = TfidfVectorizer(analyzer=content_words, sublinear_tf=True)
        self._passage_words: list[set[str]] = []

    def fit(self, texts: list[str]) -> None:
        self._char.fit(texts)
        self._word.fit(texts)
        self._passage_words = [set(content_words(t)) for t in texts]

    def _blend(self, char_part, word_part) -> np.ndarray:
        w = self.CHAR_WEIGHT
        return np.hstack([np.sqrt(w) * char_part, np.sqrt(1 - w) * word_part]).astype(np.float32)

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        return self._blend(self._char.transform(texts).toarray(), self._word.transform(texts).toarray())

    def encode_query(self, text: str) -> np.ndarray:
        return self._blend(self._char.transform([text]).toarray(), self._word.transform([text]).toarray())[0]

    def gate(self, query: str) -> np.ndarray:
        """Boolean mask over passages: True where the passage shares a content word with the query.

        Indic languages attach suffixes to words (ಯೋಜನೆಗೆ vs ಯೋಜನೆ), so a shared word also counts
        when one word starts with the other (min 3 characters)."""
        q_words = set(content_words(query))
        mask = np.zeros(len(self._passage_words), dtype=bool)
        for i, words in enumerate(self._passage_words):
            for qw in q_words:
                if qw in words or any(len(qw) >= 3 and len(pw) >= 3 and (pw.startswith(qw) or qw.startswith(pw)) for pw in words):
                    mask[i] = True
                    break
        return mask


class SentenceTransformerEmbedder:
    """Optional dense multilingual embeddings. Not used unless EMBEDDING_BACKEND=sentence-transformers."""

    name = "sentence-transformers"
    # Dense cosine scores are high even for unrelated text, so the cut-off is much higher than for
    # TF-IDF. This value is a STARTING POINT: tune it with eval/eval_retrieval.py on your machine.
    min_score = 0.80
    confident_score = 0.86
    uses_gate = False

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small"):
        from sentence_transformers import SentenceTransformer  # lazy: heavy optional dependency

        self._model = SentenceTransformer(model_name)
        self._e5 = "e5" in model_name.lower()

    def fit(self, texts: list[str]) -> None:  # nothing to fit
        return None

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        if self._e5:
            texts = [f"passage: {t}" for t in texts]
        return np.asarray(self._model.encode(texts, normalize_embeddings=True), dtype=np.float32)

    def encode_query(self, text: str) -> np.ndarray:
        prefix = "query: " if self._e5 else ""
        return np.asarray(self._model.encode([prefix + text], normalize_embeddings=True)[0], dtype=np.float32)


def make_embedder(backend: str = "tfidf", model_name: str | None = None):
    if backend == "tfidf":
        return TfidfEmbedder()
    if backend in ("sentence-transformers", "st"):
        return SentenceTransformerEmbedder(model_name or "intfloat/multilingual-e5-small")
    raise ValueError(f"Unknown EMBEDDING_BACKEND: {backend}")


# --- vector index -----------------------------------------------------------------------


class VectorIndex:
    """A small in-memory cosine-similarity index. Swap for Chroma / pgvector when the corpus grows."""

    def __init__(self, embedder, passages: list[Passage], min_score: float | None = None):
        self.embedder = embedder
        self.passages = passages
        self.min_score = embedder.min_score if min_score is None else min_score
        self.confident_score = max(embedder.confident_score, self.min_score)
        embedder.fit([p.text for p in passages])
        matrix = embedder.encode_passages([p.text for p in passages])
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        self.matrix = matrix / np.maximum(norms, 1e-9)

    def search(self, query: str, k: int = 3, lang: str | None = None, scheme_ids: set[str] | None = None) -> list[tuple[Passage, float]]:
        if not query.strip():
            return []
        q = self.embedder.encode_query(query)
        norm = np.linalg.norm(q)
        if norm < 1e-9:
            return []
        scores = self.matrix @ (q / norm)
        # Relevance gate: lexical embedders must share a content word with the query.
        allowed = self.embedder.gate(query) if getattr(self.embedder, "uses_gate", False) else None
        order = np.argsort(-scores)
        hits: list[tuple[Passage, float]] = []
        for i in order:
            passage = self.passages[i]
            if scores[i] < self.min_score:
                break  # sorted: everything after this is even less relevant
            if allowed is not None and not allowed[i]:
                continue
            if lang and passage.lang != lang:
                continue
            if scheme_ids is not None and passage.scheme_id not in scheme_ids:
                continue
            hits.append((passage, float(scores[i])))
            if len(hits) >= k:
                break
        return hits

    def scheme_scores(self, query: str, lang: str | None = None) -> dict[str, float]:
        """Best passage score per scheme: a soft 'how relevant is this scheme to what was said'."""
        best: dict[str, float] = {}
        for passage, score in self.search(query, k=len(self.passages), lang=lang):
            best[passage.scheme_id] = max(best.get(passage.scheme_id, 0.0), score)
        return best


def build_index(backend: str = "tfidf", model_name: str | None = None, min_score: float | None = None) -> VectorIndex:
    return VectorIndex(make_embedder(backend, model_name), build_passages(), min_score=min_score)
