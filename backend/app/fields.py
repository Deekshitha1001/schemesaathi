"""Profile field definitions shared by the extractor, the rule engine and the API.

Every user-facing string is available in English (en), Hindi (hi) and Kannada (kn).
The frontend uses these definitions to render the editable profile and the
follow-up questions, so adding a field here is enough to get it in the UI.
"""

from __future__ import annotations

LANGS = ("en", "hi", "kn")


def _t(en: str, hi: str, kn: str) -> dict[str, str]:
    return {"en": en, "hi": hi, "kn": kn}


YES_NO = {"true": _t("Yes", "हाँ", "ಹೌದು"), "false": _t("No", "नहीं", "ಇಲ್ಲ")}

FIELD_META: dict[str, dict] = {
    "age": {
        "type": "number",
        "label": _t("Age", "आयु", "ವಯಸ್ಸು"),
        "question": _t("How old are you?", "आपकी उम्र क्या है?", "ನಿಮ್ಮ ವಯಸ್ಸು ಎಷ್ಟು?"),
    },
    "gender": {
        "type": "enum",
        "label": _t("Gender", "लिंग", "ಲಿಂಗ"),
        "question": _t("What is your gender?", "आपका लिंग क्या है?", "ನಿಮ್ಮ ಲಿಂಗ ಯಾವುದು?"),
        "options": {
            "female": _t("Female", "महिला", "ಮಹಿಳೆ"),
            "male": _t("Male", "पुरुष", "ಪುರುಷ"),
            "other": _t("Other", "अन्य", "ಇತರೆ"),
        },
    },
    "state": {
        "type": "enum",
        "label": _t("State", "राज्य", "ರಾಜ್ಯ"),
        "question": _t("Which state do you live in?", "आप किस राज्य में रहते हैं?", "ನೀವು ಯಾವ ರಾಜ್ಯದಲ್ಲಿ ವಾಸಿಸುತ್ತೀರಿ?"),
        "options": {
            "karnataka": _t("Karnataka", "कर्नाटक", "ಕರ್ನಾಟಕ"),
            "other": _t("Another state", "अन्य राज्य", "ಬೇರೆ ರಾಜ್ಯ"),
        },
    },
    "area": {
        "type": "enum",
        "label": _t("Area", "क्षेत्र", "ಪ್ರದೇಶ"),
        "question": _t("Do you live in a village or a city?", "आप गांव में रहते हैं या शहर में?", "ನೀವು ಹಳ್ಳಿಯಲ್ಲಿ ವಾಸಿಸುತ್ತೀರಾ ಅಥವಾ ನಗರದಲ್ಲಿಯೇ?"),
        "options": {
            "rural": _t("Village / rural", "गांव / ग्रामीण", "ಹಳ್ಳಿ / ಗ್ರಾಮೀಣ"),
            "urban": _t("City / town", "शहर", "ನಗರ / ಪಟ್ಟಣ"),
        },
    },
    "annual_income": {
        "type": "number",
        "label": _t("Yearly family income (₹)", "परिवार की सालाना आय (₹)", "ಕುಟುಂಬದ ವಾರ್ಷಿಕ ಆದಾಯ (₹)"),
        "question": _t(
            "What is your family's total income in a year (in rupees)?",
            "आपके परिवार की सालाना कुल आय कितनी है (रुपये में)?",
            "ನಿಮ್ಮ ಕುಟುಂಬದ ವಾರ್ಷಿಕ ಒಟ್ಟು ಆದಾಯ ಎಷ್ಟು (ರೂಪಾಯಿಗಳಲ್ಲಿ)?",
        ),
    },
    "occupation": {
        "type": "enum",
        "label": _t("Occupation", "पेशा", "ವೃತ್ತಿ"),
        "question": _t("What work do you do?", "आप क्या काम करते हैं?", "ನೀವು ಯಾವ ಕೆಲಸ ಮಾಡುತ್ತೀರಿ?"),
        "options": {
            "farmer": _t("Farmer", "किसान", "ರೈತ"),
            "business": _t("Own business / shop", "अपना व्यवसाय / दुकान", "ಸ್ವಂತ ವ್ಯಾಪಾರ / ಅಂಗಡಿ"),
            "artisan": _t("Artisan / craftsperson", "कारीगर / शिल्पकार", "ಕುಶಲಕರ್ಮಿ"),
            "salaried": _t("Salaried job", "नौकरीपेशा", "ಸಂಬಳದ ಉದ್ಯೋಗ"),
            "labourer": _t("Daily-wage labour", "दिहाड़ी मजदूर", "ದಿನಗೂಲಿ ಕಾರ್ಮಿಕ"),
            "student": _t("Student", "विद्यार्थी", "ವಿದ್ಯಾರ್ಥಿ"),
            "unemployed": _t("Not working", "बेरोज़गार", "ನಿರುದ್ಯೋಗಿ"),
            "homemaker": _t("Homemaker", "गृहिणी", "ಗೃಹಿಣಿ"),
            "retired": _t("Retired", "सेवानिवृत्त", "ನಿವೃತ್ತ"),
        },
    },
    "ration_card": {
        "type": "enum",
        "label": _t("Ration card", "राशन कार्ड", "ಪಡಿತರ ಚೀಟಿ"),
        "question": _t("Which ration card does your family have?", "आपके परिवार के पास कौन सा राशन कार्ड है?", "ನಿಮ್ಮ ಕುಟುಂಬದ ಬಳಿ ಯಾವ ಪಡಿತರ ಚೀಟಿ ಇದೆ?"),
        "options": {
            "antyodaya": _t("Antyodaya (AAY)", "अंत्योदय (AAY)", "ಅಂತ್ಯೋದಯ (AAY)"),
            "bpl": _t("BPL", "बीपीएल (BPL)", "ಬಿಪಿಎಲ್ (BPL)"),
            "apl": _t("APL", "एपीएल (APL)", "ಎಪಿಎಲ್ (APL)"),
            "none": _t("No ration card", "राशन कार्ड नहीं है", "ಪಡಿತರ ಚೀಟಿ ಇಲ್ಲ"),
        },
    },
    "owns_agri_land": {
        "type": "bool",
        "label": _t("Owns farm land", "खेती की जमीन है", "ಕೃಷಿ ಜಮೀನು ಇದೆ"),
        "question": _t(
            "Do you or your family own agricultural land?",
            "क्या आपके या आपके परिवार के नाम खेती की जमीन है?",
            "ನಿಮ್ಮ ಅಥವಾ ನಿಮ್ಮ ಕುಟುಂಬದ ಹೆಸರಿನಲ್ಲಿ ಕೃಷಿ ಜಮೀನು ಇದೆಯೇ?",
        ),
    },
    "has_bank_account": {
        "type": "bool",
        "label": _t("Has a bank account", "बैंक खाता है", "ಬ್ಯಾಂಕ್ ಖಾತೆ ಇದೆ"),
        "question": _t("Do you have a bank account?", "क्या आपका बैंक खाता है?", "ನಿಮಗೆ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇದೆಯೇ?"),
    },
    "has_pucca_house": {
        "type": "bool",
        "label": _t("Owns a pucca house", "पक्का मकान है", "ಪಕ್ಕಾ ಮನೆ ಇದೆ"),
        "question": _t(
            "Do you own a pucca (permanent, concrete) house?",
            "क्या आपके पास अपना पक्का मकान है?",
            "ನಿಮ್ಮ ಸ್ವಂತ ಪಕ್ಕಾ (ಶಾಶ್ವತ, ಕಾಂಕ್ರೀಟ್) ಮನೆ ಇದೆಯೇ?",
        ),
    },
    "pays_income_tax": {
        "type": "bool",
        "label": _t("Pays income tax", "आयकर देते हैं", "ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿಸುತ್ತಾರೆ"),
        "question": _t(
            "Do you (or your spouse) pay income tax?",
            "क्या आप (या आपके जीवनसाथी) आयकर देते हैं?",
            "ನೀವು (ಅಥವಾ ನಿಮ್ಮ ಸಂಗಾತಿ) ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿಸುತ್ತೀರಾ?",
        ),
    },
    "govt_employee": {
        "type": "bool",
        "label": _t("Government employee", "सरकारी कर्मचारी", "ಸರ್ಕಾರಿ ನೌಕರ"),
        "question": _t("Are you a government employee?", "क्या आप सरकारी कर्मचारी हैं?", "ನೀವು ಸರ್ಕಾರಿ ನೌಕರರೇ?"),
    },
    "has_lpg": {
        "type": "bool",
        "label": _t("Has an LPG connection", "एलपीजी कनेक्शन है", "ಎಲ್‌ಪಿಜಿ ಸಂಪರ್ಕ ಇದೆ"),
        "question": _t(
            "Does your household already have an LPG gas connection?",
            "क्या आपके घर में पहले से एलपीजी गैस कनेक्शन है?",
            "ನಿಮ್ಮ ಮನೆಯಲ್ಲಿ ಈಗಾಗಲೇ ಎಲ್‌ಪಿಜಿ ಗ್ಯಾಸ್ ಸಂಪರ್ಕ ಇದೆಯೇ?",
        ),
    },
    "girl_child_under_10": {
        "type": "bool",
        "label": _t("Daughter under 10", "10 साल से कम की बेटी", "10 ವರ್ಷದೊಳಗಿನ ಮಗಳು"),
        "question": _t(
            "Do you have a daughter below 10 years of age?",
            "क्या आपकी 10 साल से कम उम्र की बेटी है?",
            "ನಿಮಗೆ 10 ವರ್ಷಕ್ಕಿಂತ ಕಡಿಮೆ ವಯಸ್ಸಿನ ಮಗಳಿದ್ದಾಳೆಯೇ?",
        ),
    },
    "household_head": {
        "type": "bool",
        "label": _t("Head of family", "परिवार की मुखिया/मुखिया", "ಕುಟುಂಬದ ಯಜಮಾನ/ಯಜಮಾನಿ"),
        "question": _t(
            "Are you the head of your family (household)?",
            "क्या आप अपने परिवार के मुखिया हैं?",
            "ನೀವು ನಿಮ್ಮ ಕುಟುಂಬದ ಯಜಮಾನರೇ (ಮುಖ್ಯಸ್ಥರೇ)?",
        ),
    },
    "traditional_trade": {
        "type": "bool",
        "label": _t("Traditional trade", "पारंपरिक कारीगरी", "ಸಾಂಪ್ರದಾಯಿಕ ಕಸುಬು"),
        "question": _t(
            "Do you work in a traditional trade such as carpenter, blacksmith, goldsmith, potter, "
            "sculptor, cobbler, mason, basket/mat/broom maker, toy maker, barber, garland maker, "
            "washerman, tailor, or boat/fishing-net maker?",
            "क्या आप बढ़ई, लोहार, सुनार, कुम्हार, मूर्तिकार, मोची, राजमिस्त्री, टोकरी/चटाई/झाड़ू बनाने वाले, "
            "खिलौना बनाने वाले, नाई, माली (माला बनाने वाले), धोबी, दर्जी या नाव/जाल बनाने वाले जैसे पारंपरिक काम करते हैं?",
            "ನೀವು ಬಡಗಿ, ಕಮ್ಮಾರ, ಅಕ್ಕಸಾಲಿ, ಕುಂಬಾರ, ಶಿಲ್ಪಿ, ಚಮ್ಮಾರ, ಮೇಸ್ತ್ರಿ, ಬುಟ್ಟಿ/ಚಾಪೆ/ಪೊರಕೆ ತಯಾರಕ, "
            "ಆಟಿಕೆ ತಯಾರಕ, ಕ್ಷೌರಿಕ, ಹೂಮಾಲೆ ತಯಾರಕ, ಅಗಸ, ದರ್ಜಿ ಅಥವಾ ದೋಣಿ/ಮೀನುಬಲೆ ತಯಾರಕ ಮುಂತಾದ ಸಾಂಪ್ರದಾಯಿಕ ಕಸುಬು ಮಾಡುತ್ತೀರಾ?",
        ),
    },
}

FIELD_ORDER = list(FIELD_META)


def public_meta() -> dict:
    """What the frontend needs to render forms and labels."""
    return {"fields": FIELD_META, "order": FIELD_ORDER, "yes_no": YES_NO, "languages": list(LANGS)}


def clean_value(field: str, value):
    """Validate a raw value against FIELD_META; return the clean value or None if invalid."""
    meta = FIELD_META.get(field)
    if meta is None or value is None or value == "":
        return None
    kind = meta["type"]
    if kind == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ("true", "false"):
            return value.lower() == "true"
        return None
    if kind == "number":
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number < 0:
            return None
        if field == "age" and not (0 < number < 121):
            return None
        return int(number) if number == int(number) else number
    if kind == "enum":
        return value if isinstance(value, str) and value in meta["options"] else None
    return None


def clean_profile(raw: dict | None) -> dict:
    """Keep only known fields with valid values."""
    out = {}
    for field, value in (raw or {}).items():
        cleaned = clean_value(field, value)
        if cleaned is not None:
            out[field] = cleaned
    return out
