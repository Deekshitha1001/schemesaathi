"""Rule-based profile extractor for English, Hindi and Kannada text.

This is the offline baseline: it needs no model and no API key, so the app works
(and can be tested) without any network access. When an LLM is configured, the
service layer asks the LLM for the same JSON and merges the two (see service.py).

Design choices worth knowing about:
* Only facts that are stated are extracted. Silence means "unknown" (None), never False.
* Negation is handled ("no bank account", "बैंक खाता नहीं है", "ಬ್ಯಾಂಕ್ ಖಾತೆ ಇಲ್ಲ").
* Income needs a period (monthly/yearly). If it is ambiguous we do NOT guess;
  we leave it unknown and report a warning so the UI can ask.
* Indian digits (Devanagari / Kannada) and Indian comma grouping (1,50,000) are supported.
  Numbers written as words ("पचास हज़ार") are not parsed yet.
"""

from __future__ import annotations

import re
import unicodedata

from .fields import clean_profile

# --- normalisation ---------------------------------------------------------------

_DIGIT_MAP = {ord(c): str(i) for i, c in enumerate("०१२३४५६७८९")}
_DIGIT_MAP.update({ord(c): str(i) for i, c in enumerate("೦೧೨೩೪೫೬೭೮೯")})


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = text.replace("‌", "").replace("‍", "")  # ZWNJ / ZWJ
    text = text.translate(_DIGIT_MAP)
    text = text.replace("ँ", "ं")  # chandrabindu -> anusvara so हूँ == हूं
    text = text.replace("’", "'").replace("‘", "'")
    return text.lower()


def _rx(*patterns: str) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


def _is_indic(s: str) -> bool:
    return any("ऀ" <= ch <= "෿" for ch in s)


# --- age ---------------------------------------------------------------------------

_YEAR_UNIT = r"(?:years?\s*old|year-old|years?|yrs?|yo\b|वर्ष|साल|बरस|ವರ್ಷ|ವರುಷ)"
_AGE_WORDS = r"(?:i am|i'm|im|age|aged|age is|उम्र|आयु|ವಯಸ್ಸು|ವಯಸ್ಸಿನ|ನನಗೆ|मैं|मेरी)"
_CHILD_WORDS = _rx(
    r"daughter", r"girl child", r"baby girl", r"\bson\b", r"\bchild", r"\bkids?\b", r"granddaughter",
    r"बेटी", r"बेटा", r"बच्ची", r"बच्चे", r"बच्चा", r"ಮಗಳ", r"ಮಗನ", r"ಮಗು", r"ಮಕ್ಕಳ", r"ಮೊಮ್ಮಗಳ",
)
_RELATIVE_WORDS = _rx(
    r"\b(?:father|mother|husband|wife|brother|sister|parents?|grand(?:father|mother)|in-laws?)\b",
    r"पिता", r"माता", r"पति", r"पत्नी", r"भाई", r"बहन", r"ससुर", r"सास",
    r"ತಂದೆ", r"ತಾಯಿ", r"ಪತಿ", r"ಪತ್ನಿ", r"ಗಂಡ", r"ಹೆಂಡತಿ", r"ಅಣ್ಣ", r"ತಮ್ಮ", r"ಅಕ್ಕ", r"ತಂಗಿ",
)
_OTHER_PERSON = re.compile(f"{_CHILD_WORDS.pattern}|{_RELATIVE_WORDS.pattern}", re.IGNORECASE)
_CHILD_AFTER = re.compile(rf"^\s*(?:{_YEAR_UNIT})?\s*(?:की|का|के|old)?\s*(?:{_CHILD_WORDS.pattern})", re.IGNORECASE)
_SPEAKER_IS_CHILD = re.compile(r"(?:\bi am|\bi'm|\bim)\s+(?:(?:a|the|her|his|their|an|only)\s+)?$")
_NON_AGE_CONTEXT = _rx(r"experience", r"farming for", r"अनुभव", r"ಅನುಭವ", r"married", r"for\s*$")


def extract_age(text: str) -> int | None:
    """The speaker's own age.

    Numbers can belong to the speaker, a child ("my daughter is 6 years old") or
    something else ("5 years of farming"). Each child word "claims" the nearest
    number, and an explicit self-age ("I am 33", "उम्र 40", "ನನಗೆ 34") is protected
    from that claim unless a child word sits right before it ("daughter's age 6").
    """
    found: dict[tuple[int, int], dict] = {}  # number span -> {"value", "score", "explicit"}

    def add(m: re.Match, explicit: bool) -> None:
        value = int(m.group(1))
        if not 0 < value < 121:
            return
        span = m.span(1)
        score = 2 if explicit else 1
        if not explicit and _NON_AGE_CONTEXT.search(text[max(0, m.start() - 14): m.end() + 24]):
            score -= 2  # "20 years of farming experience", "married for 5 years"
        entry = found.get(span)
        if entry is None or score > entry["score"]:
            found[span] = {"value": value, "score": score, "explicit": explicit or (entry and entry["explicit"])}

    for m in re.finditer(rf"(\d{{1,3}})\s*{_YEAR_UNIT}", text):
        add(m, explicit=False)
    for m in re.finditer(rf"{_AGE_WORDS}\D{{0,8}}?(\d{{1,3}})\b", text):
        # "daughter's age 6" is not the speaker's age; "I have a son. I am 30" is.
        lead = re.split(r"[.।!?\n]", text[max(0, m.start() - 14): m.start(1)])[-1]
        child_follows = bool(_CHILD_AFTER.match(text[m.end(1): m.end(1) + 24]))
        add(m, explicit=not _OTHER_PERSON.search(lead) and not child_follows)

    # Each child / relative word claims the nearest number within 40 characters.
    for child in _OTHER_PERSON.finditer(text):
        if _SPEAKER_IS_CHILD.search(text[max(0, child.start() - 16): child.start()]):
            continue
        nearest, best_gap = None, 41
        for span, entry in found.items():
            gap = min(abs(span[0] - child.end()), abs(child.start() - span[1]))
            if gap < best_gap:
                nearest, best_gap = span, gap
        if nearest is None or found[nearest]["explicit"]:
            continue
        # A number inside a sentence that speaks in the first person ("I am her son, 38 years old")
        # is the speaker's, even when a relative was mentioned in the previous sentence.
        sentence_start = max(text.rfind(c, 0, nearest[0]) for c in ".।!?\n") + 1
        lead_in = text[sentence_start: nearest[0]]
        others = [m for m in _OTHER_PERSON.finditer(lead_in)
                  if not _SPEAKER_IS_CHILD.search(lead_in[max(0, m.start() - 16): m.start()])]  # "I am her SON" is the speaker
        if _SELF.search(lead_in) and not others:
            continue
        found[nearest]["score"] = -1

    ok = [e for e in found.values() if e["score"] >= 0]
    return max(ok, key=lambda e: e["score"])["value"] if ok else None


# --- gender ------------------------------------------------------------------------

_FEMALE = _rx(
    r"\bwoman\b", r"\bwomen\b", r"\bfemale\b", r"\blady\b", r"\bwidow", r"\bhousewife\b", r"single mother",
    r"\bi am a mother\b", r"\bi'm a mother\b",
    r"महिला", r"औरत", r"स्त्री", r"विधवा", r"गृहिणी", r"(?:रही|करती|वाली|चुकी)\s*हूं", r"ती\s*हूं",
    r"ಮಹಿಳೆ", r"ಸ್ತ್ರೀ", r"ವಿಧವೆ", r"ಗೃಹಿಣಿ", r"ಹೆಣ್ಣು(?!\s*ಮಗು)",
)
_MALE = _rx(
    r"\bman\b", r"\bmale\b", r"\bgentleman\b",
    r"पुरुष", r"आदमी", r"(?:रहा|करता|वाला)\s*हूं", r"ता\s*हूं",
    r"ಪುರುಷ", r"ಗಂಡಸು", r"ಗಂಡು(?!\s*ಮಗು)",
)


def extract_gender(text: str) -> str | None:
    if _FEMALE.search(text):
        return "female"
    if _MALE.search(text):
        return "male"
    return None


# --- income ------------------------------------------------------------------------

_INCOME_KW = _rx(
    r"income", r"\bearn", r"salary", r"\bwages?\b", r"आय\b", r"आमदनी", r"कमाई", r"कमाता", r"कमाती", r"कमाते", r"तनख्वाह", r"वेतन", r"मजदूरी",
    r"ಆದಾಯ", r"ಸಂಬಳ", r"ಗಳಿಕೆ", r"ಗಳಿಸ", r"ಕೂಲಿ",
)
_MULT = {
    "lakh": 100_000, "lakhs": 100_000, "lac": 100_000, "lacs": 100_000, "लाख": 100_000, "ಲಕ್ಷ": 100_000,
    "crore": 10_000_000, "करोड़": 10_000_000, "ಕೋಟಿ": 10_000_000,
    "thousand": 1_000, "k": 1_000, "हज़ार": 1_000, "हजार": 1_000, "ಸಾವಿರ": 1_000,
}
_MONEY = re.compile(
    r"(?P<cur1>₹|rs\.?|inr)?\s*(?P<num>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?P<mult>lakhs?|lacs?|crore|thousand|k\b|लाख|करोड़|हज़ार|हजार|ಲಕ್ಷ|ಕೋಟಿ|ಸಾವಿರ)?\s*"
    r"(?P<cur2>rupees|rupee|rs\b|रुपये|रुपए|रुपया|ರೂಪಾಯಿ|ರೂ\b)?"
)
_MONTHLY = _rx(r"per month", r"a month", r"monthly", r"/\s*month", r"each month", r"every month", r"महीने", r"मासिक", r"माह", r"ತಿಂಗಳು", r"ತಿಂಗಳಿಗೆ", r"ತಿಂಗಳ", r"ಮಾಸಿಕ")
_YEARLY = _rx(r"per year", r"a year", r"yearly", r"annual", r"per annum", r"/\s*year", r"सालाना", r"वार्षिक", r"साल में", r"प्रति वर्ष", r"ವಾರ್ಷಿಕ", r"ವರ್ಷಕ್ಕೆ")
_DAILY = _rx(r"per day", r"a day", r"daily", r"/\s*day", r"रोज़", r"रोज", r"दैनिक", r"प्रतिदिन", r"ದಿನಕ್ಕೆ", r"ದಿನದ", r"ದಿನಗೂಲಿ")


def extract_income(text: str) -> tuple[int | None, str | None]:
    """Returns (annual_income, warning). warning is 'income_period_unclear' or 'income_daily'."""
    best = None  # (distance, annual_value, warning)
    keywords = [m.span() for m in _INCOME_KW.finditer(text)]
    if not keywords:
        return None, None

    for m in _MONEY.finditer(text):
        raw = m.group("num").replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        mult = (m.group("mult") or "").lower()
        has_currency = bool(m.group("cur1") or m.group("cur2"))
        start, end = m.span()

        # Skip ages and other small plain numbers that are not money.
        tail = text[end: end + 14]
        if not has_currency and not mult and re.match(rf"\s*{_YEAR_UNIT}", tail):
            continue
        if not mult and not has_currency and value < 1000:
            continue

        distance = min(min(abs(start - ke), abs(ks - end)) for ks, ke in keywords)
        if distance > 40:
            continue

        amount = value * _MULT.get(mult, 1)
        window = text[max(0, start - 30): end + 30]
        warning = None
        if _DAILY.search(window) and not _MONTHLY.search(window) and not _YEARLY.search(window):
            annual, warning = None, "income_daily"
        elif _MONTHLY.search(window) and not _YEARLY.search(window):
            annual = amount * 12
        elif _YEARLY.search(window) or mult in ("lakh", "lakhs", "lac", "lacs", "crore") or mult in ("लाख", "ಲಕ್ಷ", "करोड़", "ಕೋಟಿ"):
            annual = amount
        elif amount >= 100_000:  # nobody earns this per month in the target group; assume yearly
            annual = amount
        else:
            annual, warning = None, "income_period_unclear"

        if best is None or distance < best[0]:
            best = (distance, annual, warning)

    if best is None:
        return None, None
    annual, warning = best[1], best[2]
    return (int(annual) if annual is not None else None), warning


# --- state / area ---------------------------------------------------------------------

_KARNATAKA = _rx(r"karnataka", r"bengaluru", r"bangalore", r"mysuru", r"mysore", r"mangaluru", r"mangalore", r"hubballi", r"hubli", r"belagavi", r"belgaum", r"kalaburagi", r"ballari", r"davangere", r"shivamogga", r"tumakuru",
                 r"कर्नाटक", r"बेंगलुरु", r"बेंगलोर", r"मैसूर", r"ಕರ್ನಾಟಕ", r"ಬೆಂಗಳೂರ", r"ಮೈಸೂರ", r"ಮಂಗಳೂರ", r"ಹುಬ್ಬಳ್ಳಿ", r"ಬೆಳಗಾವಿ", r"ಕಲಬುರಗಿ", r"ಬಳ್ಳಾರಿ", r"ದಾವಣಗೆರೆ", r"ಶಿವಮೊಗ್ಗ", r"ತುಮಕೂರ")
_OTHER_STATE = _rx(r"tamil nadu", r"kerala", r"andhra", r"telangana", r"maharashtra", r"gujarat", r"uttar pradesh", r"bihar", r"rajasthan", r"madhya pradesh", r"west bengal", r"odisha", r"punjab", r"haryana", r"assam", r"jharkhand", r"chhattisgarh", r"delhi", r"mumbai", r"chennai", r"hyderabad",
                   r"तमिलनाडु", r"केरल", r"आंध्र", r"तेलंगाना", r"महाराष्ट्र", r"गुजरात", r"उत्तर प्रदेश", r"बिहार", r"राजस्थान", r"मध्य प्रदेश", r"पश्चिम बंगाल", r"ओडिशा", r"पंजाब", r"हरियाणा", r"दिल्ली", r"मुंबई",
                   r"ತಮಿಳುನಾಡು", r"ಕೇರಳ", r"ಆಂಧ್ರ", r"ತೆಲಂಗಾಣ", r"ಮಹಾರಾಷ್ಟ್ರ", r"ಗುಜರಾತ್", r"ದೆಹಲಿ", r"ಮುಂಬೈ", r"ಚೆನ್ನೈ", r"ಹೈದರಾಬಾದ್")


def extract_state(text: str) -> str | None:
    if _KARNATAKA.search(text):
        return "karnataka"
    if _OTHER_STATE.search(text):
        return "other"
    return None


_RURAL = _rx(r"village", r"\brural\b", r"गांव", r"गाँव", r"ग्रामीण", r"ಹಳ್ಳಿ", r"ಗ್ರಾಮ")
_URBAN = _rx(r"\bcity\b", r"\burban\b", r"\btown\b", r"शहर", r"ಶಹರ", r"ನಗರ", r"ಪಟ್ಟಣ")


def extract_area(text: str) -> str | None:
    rural, urban = bool(_RURAL.search(text)), bool(_URBAN.search(text))
    if rural and not urban:
        return "rural"
    if urban and not rural:
        return "urban"
    return None


# --- occupation ----------------------------------------------------------------------

_OCCUPATIONS = {
    "farmer": _rx(r"\bfarmer", r"\bfarming\b", r"cultivat", r"agricultur", r"\bkisan\b", r"किसान", r"खेती", r"काश्तकार", r"ರೈತ", r"ಕೃಷಿ", r"ಬೇಸಾಯ"),
    "business": _rx(r"\bshop\b", r"\bbusiness\b", r"\bvendor\b", r"\btrader\b", r"\bstall\b", r"दुकान", r"व्यापार", r"व्यवसाय", r"कारोबार", r"ಅಂಗಡಿ", r"ವ್ಯಾಪಾರ", r"ವ್ಯವಹಾರ"),
    "artisan": _rx(r"\bweaver", r"\bartisan", r"\bcraft", r"\bpotter", r"\bcarpenter", r"\btailor", r"\bblacksmith", r"\bgoldsmith", r"\bcobbler", r"\bmason\b", r"\bbarber",
                   r"कारीगर", r"बुनकर", r"दर्जी", r"कुम्हार", r"बढ़ई", r"लोहार", r"सुनार", r"मोची", r"राजमिस्त्री", r"नाई\b", r"ಕುಶಲಕರ್ಮಿ", r"ನೇಕಾರ", r"ಟೈಲರ್", r"ದರ್ಜಿ", r"ಕುಂಬಾರ", r"ಬಡಗಿ", r"ಕಮ್ಮಾರ", r"ಅಕ್ಕಸಾಲಿ", r"ಚಮ್ಮಾರ", r"ಕ್ಷೌರಿಕ", r"ಮೇಸ್ತ್ರಿ", r"ಹೊಲಿಗೆ"),
    "unemployed": _rx(r"unemployed", r"jobless", r"no job", r"not working", r"बेरोज़गार", r"बेरोजगार", r"ನಿರುದ್ಯೋಗಿ"),
    "salaried": _rx(r"salaried", r"\bemployee\b", r"private job", r"नौकरी", r"कर्मचारी", r"ನೌಕರ", r"ಉದ್ಯೋಗಿ"),
    "labourer": _rx(r"labou?r", r"daily wage", r"coolie", r"मजदूर", r"दिहाड़ी", r"ಕೂಲಿ", r"ಕಾರ್ಮಿಕ"),
    "student": _rx(r"\bstudent", r"छात्र", r"विद्यार्थी", r"ವಿದ್ಯಾರ್ಥಿ"),
    "homemaker": _rx(r"housewife", r"homemaker", r"गृहिणी", r"ಗೃಹಿಣಿ"),
    "retired": _rx(r"retired", r"pensioner", r"सेवानिवृत्त", r"ನಿವೃತ್ತ"),
}


def extract_occupation(text: str) -> str | None:
    """Earliest-mentioned occupation wins ('farmer' in 'I am a farmer and my son has a shop')."""
    found = []
    for name, pattern in _OCCUPATIONS.items():
        for m in pattern.finditer(text):
            if not _belongs_to_relative(text, m):
                found.append((m.start(), name))
                break
    return min(found)[1] if found else None


# --- ration card ---------------------------------------------------------------------

_NO_RATION = _rx(r"no ration card", r"(?:don't|do not|dont) have (?:a |any )?ration card", r"without (?:a )?ration card", r"राशन कार्ड[^।.]{0,12}नहीं", r"ಪಡಿತರ ಚೀಟಿ[^.]{0,12}ಇಲ್ಲ", r"ರೇಷನ್ ಕಾರ್ಡ್[^.]{0,12}ಇಲ್ಲ")
_ANTYODAYA = _rx(r"antyodaya", r"\baay\b", r"अंत्योदय", r"ಅಂತ್ಯೋದಯ")
_BPL = _rx(r"\bbpl\b", r"below poverty", r"बीपीएल", r"गरीबी रेखा", r"ಬಿಪಿಎಲ್", r"ಬಡತನ ರೇಖೆ")
_APL = _rx(r"\bapl\b", r"एपीएल", r"ಎಪಿಎಲ್")


def extract_ration_card(text: str) -> str | None:
    if _NO_RATION.search(text):
        return "none"
    if _ANTYODAYA.search(text):
        return "antyodaya"
    if _BPL.search(text):
        return "bpl"
    if _APL.search(text):
        return "apl"
    return None


# --- yes/no facts with negation -------------------------------------------------------

_NEG_BEFORE = re.compile(r"(?:\bno\b|\bnot\b|don't|dont|do not|doesn't|does not|without|never|\bnor\b|n't)\s*(?:\w+\s+){0,3}$")
_NEG_AFTER_INDIC = re.compile(r"^(?:(?!और|तथा|ಮತ್ತು)[^।.,;\n]){0,22}?(?:नहीं|नही|ಇಲ್ಲ|ದಿಲ್ಲ|ಅಲ್ಲ|ಇಲ್ಲದ)")


def _negated(text: str, match: re.Match) -> bool:
    keyword = match.group(0)
    if _is_indic(keyword):
        return bool(_NEG_AFTER_INDIC.match(text[match.end(): match.end() + 30]))
    return bool(_NEG_BEFORE.search(text[max(0, match.start() - 24): match.start()]))


_SELF = re.compile(r"\bi\b|\bi'm\b|\bim\b|मैं|मेरा|मेरी|मुझे|ನಾನು|ನನಗೆ|ನನ್ನ")
_SPOUSE = re.compile(r"husband|wife|spouse|पति|पत्नी|ಪತಿ|ಪತ್ನಿ|ಗಂಡ|ಹೆಂಡತಿ")


def _belongs_to_relative(text: str, match: re.Match, spouse_counts: bool = False) -> bool:
    """True if the matched phrase describes someone else ("My father is a government employee").

    A relative word earlier in the same sentence, with no first-person word in between, owns the fact.
    """
    sentence_start = max(text.rfind(c, 0, match.start()) for c in ".।!?\n") + 1
    before = text[sentence_start: match.start()]
    relatives = list(_RELATIVE_WORDS.finditer(before))
    if not relatives:
        return False
    last = relatives[-1]
    if len(before) - last.end() > 45 or _SELF.search(before[last.end():]):
        return False
    return not (spouse_counts and _SPOUSE.search(last.group(0)))


def _fact(text: str, positive: re.Pattern, *, direct_false: re.Pattern | None = None, direct_true: re.Pattern | None = None,
          skip_relatives: bool = False, spouse_counts: bool = False) -> bool | None:
    """True/False/None for a yes-no fact.

    direct_false / direct_true: phrases that settle it on their own (e.g. 'landless').
    positive: a phrase meaning "has X"; if it is negated nearby the answer is False.
    skip_relatives: ignore mentions that are about a relative, not the speaker.
    spouse_counts: with skip_relatives, a spouse's fact still counts (e.g. income tax is judged per couple).
    """
    if direct_false and direct_false.search(text):
        return False
    if direct_true and direct_true.search(text):
        return True
    for m in positive.finditer(text):
        if skip_relatives and _belongs_to_relative(text, m, spouse_counts):
            continue
        return not _negated(text, m)
    return None


_LAND_POS = _rx(r"\bacres?\b", r"\bhectares?\b", r"own (?:\w+ )?land", r"my (?:own )?(?:land|farm)\b", r"एकड़", r"जमीन", r"खेत(?!ी)", r"भूमि(?!हीन)", r"ಎಕರೆ", r"ಜಮೀನ", r"ಭೂಮಿ")
_LAND_NO = _rx(r"landless", r"(?:no|without) (?:\w+ )?land", r"tenant", r"leased? (?:the )?land", r"sharecropp", r"भूमिहीन", r"बटाई", r"ಭೂರಹಿತ", r"ಜಮೀನು ಇಲ್ಲ", r"ಭೂಮಿ ಇಲ್ಲ", r"ಗುತ್ತಿಗೆ")
_BANK_POS = _rx(r"bank account", r"savings account", r"jan ?dhan", r"बैंक खाता", r"जन ?धन", r"ಬ್ಯಾಂಕ್ ಖಾತೆ", r"ಜನ್ ?ಧನ್", r"ಬ್ಯಾಂಕ್ ಅಕೌಂಟ್")
_HOUSE_POS = _rx(r"pucca", r"concrete house", r"permanent house", r"पक्का (?:मकान|घर)", r"ಪಕ್ಕಾ ಮನೆ")
_HOUSE_NO = _rx(r"kutcha", r"kachcha", r"kaccha", r"mud house", r"thatched", r"\bhut\b", r"no house", r"homeless", r"rented house", r"live (?:on|in) rent", r"कच्चा", r"झोपड़ी", r"मकान नहीं", r"घर नहीं", r"किराये", r"किराए", r"ಕಚ್ಚಾ", r"ಗುಡಿಸಲು", r"ಮನೆ ಇಲ್ಲ", r"ಬಾಡಿಗೆ ಮನೆ")
_TAX_POS = _rx(r"income tax", r"tax ?payer", r"\bitr\b", r"आयकर", r"इनकम टैक्स", r"ಆದಾಯ ತೆರಿಗೆ", r"ಇನ್ಕಮ್ ಟ್ಯಾಕ್ಸ್")
_GOVT_POS = _rx(r"government (?:job|employee|servant|service)", r"govt\.? (?:job|employee|servant|service)", r"सरकारी (?:नौकरी|कर्मचारी)", r"ಸರ್ಕಾರಿ (?:ನೌಕರ|ಉದ್ಯೋಗ)")
_LPG_POS = _rx(r"\blpg\b", r"gas (?:connection|cylinder|stove)", r"cylinder", r"गैस (?:कनेक्शन|सिलेंडर)", r"सिलेंडर", r"ಎಲ್ಪಿಜಿ", r"ಗ್ಯಾಸ್", r"ಸಿಲಿಂಡರ್")
_LPG_NO = _rx(r"firewood", r"chulha", r"wood stove", r"cook(?:ing)? on wood", r"लकड़ी", r"चूल्हा", r"उपले", r"ಸೌದೆ", r"ಕಟ್ಟಿಗೆ ಒಲೆ")
_HEAD_POS = _rx(r"head of (?:the |my )?(?:family|household)", r"(?:family|household) head", r"only earning member", r"main earner", r"मुखिया", r"परिवार की प्रमुख", r"ಯಜಮಾನಿ", r"ಯಜಮಾನ", r"ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥ")
_OTHER_HEAD = _rx(r"(?:husband|father|brother|son)\s+(?:is|as)\s+(?:the\s+)?head", r"(?:पति|पिता|भाई)[^।.]{0,12}मुखिया", r"(?:ಪತಿ|ಗಂಡ|ತಂದೆ)[^.]{0,14}(?:ಯಜಮಾನ|ಮುಖ್ಯಸ್ಥ)")
_TRADE = _rx(r"\btailor", r"\bpotter", r"\bcarpenter", r"\bblacksmith", r"\bgoldsmith", r"\bcobbler", r"\bmason\b", r"\bbarber", r"sculptor", r"washerman", r"dhobi", r"locksmith", r"garland", r"toy maker", r"boat ?maker", r"basket", r"broom",
             r"दर्जी", r"कुम्हार", r"बढ़ई", r"लोहार", r"सुनार", r"मोची", r"राजमिस्त्री", r"नाई\b", r"मूर्तिकार", r"धोबी", r"टोकरी", r"ಟೈಲರ್", r"ದರ್ಜಿ", r"ಕುಂಬಾರ", r"ಬಡಗಿ", r"ಕಮ್ಮಾರ", r"ಅಕ್ಕಸಾಲಿ", r"ಚಮ್ಮಾರ", r"ಕ್ಷೌರಿಕ", r"ಮೇಸ್ತ್ರಿ", r"ಶಿಲ್ಪಿ", r"ಅಗಸ", r"ಬುಟ್ಟಿ", r"ಹೊಲಿಗೆ")

_DAUGHTER = _rx(r"daughter", r"girl child", r"baby girl", r"बेटी", r"बच्ची", r"ಮಗಳ", r"ಹೆಣ್ಣು ಮಗು", r"ಹೆಣ್ಣುಮಗು")
_AGE_NEAR = re.compile(rf"(\d{{1,2}})\s*(?P<unit>{_YEAR_UNIT}|months?|महीने|ತಿಂಗಳ)")


def extract_girl_child(text: str) -> bool | None:
    """True if a daughter under 10 is mentioned; False if her age is given as 10+; else None."""
    for m in _DAUGHTER.finditer(text):
        bare = re.match(r"[^\d.।!?\n]{0,14}?(\d{1,2})(?!\d)(?!\s*(?:acres?|rupees|rs|%|लाख|हज़ार|हजार|ಲಕ್ಷ|ಸಾವಿರ))", text[m.end(): m.end() + 24])
        if bare and not re.match(r"\s*(?:months?|महीने|ತಿಂಗಳ)", text[m.end() + bare.end(1): m.end() + bare.end(1) + 8]):
            return int(bare.group(1)) < 10
        window_start, window_end = max(0, m.start() - 30), m.end() + 30
        best = None
        for a in _AGE_NEAR.finditer(text, window_start, window_end):
            gap = min(abs(a.start() - m.end()), abs(m.start() - a.end()))
            if best is None or gap < best[0]:
                unit = a.group("unit")
                is_months = unit in ("month", "months", "महीने", "ತಿಂಗಳ")
                best = (gap, 0 if is_months else int(a.group(1)))
        if best is not None:
            return best[1] < 10
    return None


def extract_profile(raw_text: str) -> dict:
    """Extract a profile from free text.

    Returns {"profile": {...}, "warnings": [...]} where profile only contains stated facts.
    """
    text = normalize(raw_text)
    warnings: list[str] = []
    profile: dict = {}

    profile["age"] = extract_age(text)
    profile["gender"] = extract_gender(text)
    income, warning = extract_income(text)
    profile["annual_income"] = income
    if warning:
        warnings.append(warning)
    profile["state"] = extract_state(text)
    profile["area"] = extract_area(text)
    profile["occupation"] = extract_occupation(text)
    profile["ration_card"] = extract_ration_card(text)

    profile["owns_agri_land"] = _fact(text, _LAND_POS, direct_false=_LAND_NO)
    profile["has_bank_account"] = _fact(text, _BANK_POS, skip_relatives=True)
    profile["has_pucca_house"] = _fact(text, _HOUSE_POS, direct_false=_HOUSE_NO)
    profile["pays_income_tax"] = _fact(text, _TAX_POS, skip_relatives=True, spouse_counts=True)
    profile["govt_employee"] = _fact(text, _GOVT_POS, skip_relatives=True)
    profile["has_lpg"] = _fact(text, _LPG_POS, direct_false=_LPG_NO)
    profile["household_head"] = _fact(text, _HEAD_POS, direct_false=_OTHER_HEAD)
    profile["traditional_trade"] = True if _TRADE.search(text) else None
    profile["girl_child_under_10"] = extract_girl_child(text)

    # A housewife is, by definition, a woman who is not in paid work.
    if profile["occupation"] == "homemaker" and profile["gender"] is None:
        profile["gender"] = "female"
    if profile["govt_employee"] is True and profile["occupation"] is None:
        profile["occupation"] = "salaried"

    return {"profile": clean_profile({k: v for k, v in profile.items() if v is not None}), "warnings": warnings}
