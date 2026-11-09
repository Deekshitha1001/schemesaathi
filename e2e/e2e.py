"""Browser end-to-end test (Playwright + Chromium): types a description, checks results, follow-up questions,
profile editing, the Ask box, Hindi / Kannada UI, error messages, mobile layout and basic accessibility.

Run the whole app from ONE process so the UI and the API share an origin:

    cd frontend && npm install && npm run build
    cd ../backend && SERVE_FRONTEND_DIR=../frontend/dist uvicorn app.main:app --port 8000
    pip install playwright && playwright install chromium
    python e2e/e2e.py                      # or:  BASE_URL=http://localhost:8080 python e2e/e2e.py   (docker compose)

Screenshots are written to e2e/shots/. Browser console will show a few "Failed to load resource" errors:
those are the requests this test blocks on purpose (web fonts, a simulated outage, a simulated 429).
It was developed against the same SchemeService behind a Starlette stand-in server (FastAPI could not be
installed in the build sandbox), so a failure against the real FastAPI app is worth investigating.
"""
import os
import json, sys
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
SHOTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(SHOTS, exist_ok=True)
results, console_errors, page_errors = [], [], []

def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1100, "height": 900}, locale="en-IN")
    page = ctx.new_page()
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    # Fonts are loaded from Google Fonts; the sandbox has no internet, so ignore those failures only.
    page.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    page.route("**/fonts.gstatic.com/**", lambda r: r.abort())

    page.goto(BASE)
    check("page title", "SchemeSaathi" in page.title())
    check("html lang is en", page.evaluate("document.documentElement.lang") == "en")
    check("hero heading", page.locator("h1").inner_text().startswith("Which government schemes"))
    check("find button disabled when empty", page.get_by_role("button", name="Find my schemes").is_disabled())

    # --- English flow via the example chip
    page.get_by_role("button", name="I am a 45 year old farmer woman").click()
    check("example fills textarea", "45 year old farmer woman" in page.locator("#situation").input_value())
    page.get_by_role("button", name="Find my schemes").click()
    page.wait_for_selector("h2.results-h")
    check("results heading focused", page.evaluate("document.activeElement.className") == "results-h")
    check("unverified-data banner shown", page.get_by_text("Demo data").is_visible())
    chips = page.locator(".summary-chips li").all_inner_texts()
    check("summary chips show counts", len(chips) == 3 and all(c.strip()[0].isdigit() for c in chips), str(chips))
    facts = page.locator(".facts").inner_text()
    for needle in ("45", "Female", "Karnataka", "Farmer", "BPL", "₹80,000"):
        check(f"profile shows {needle}", needle in facts, facts[:200])
    check("PM-KISAN card present", page.locator("#scheme-pm_kisan").count() == 1)
    check("not-eligible group collapsed", page.locator("details.group-closed").get_attribute("open") is None)
    page.screenshot(path=f"{SHOTS}/01-english-results.png", full_page=True)

    # --- follow-up question flips a scheme to eligible
    before = page.locator("#scheme-pm_kisan .badge.status-likely, #scheme-pm_kisan .badge.status-eligible").first.inner_text()
    q_count_before = page.locator(".questions li").count()
    check("follow-up questions shown, at most 4", 0 < q_count_before <= 4, str(q_count_before))
    tax_q = page.locator(".questions li", has_text="income tax").first
    tax_q.get_by_role("button", name="No").click()
    page.wait_for_function("![...document.querySelectorAll('.questions li')].some(li => li.innerText.includes('income tax'))")
    check("answered question disappears from the list", True)
    page.wait_for_timeout(300)
    govt_q = page.locator(".questions li", has_text="government employee")
    if govt_q.count():
        govt_q.first.get_by_role("button", name="No").click()
        page.wait_for_function("![...document.querySelectorAll('.questions li')].some(li => li.innerText.includes('government employee'))")
    page.wait_for_function("document.querySelector('#scheme-pm_kisan .badge').innerText.includes('Appears to qualify')")
    check("answering questions makes PM-KISAN 'Appears to qualify'", True)
    check("answered fact shows 'set by you'", "set by you" in page.locator(".facts").inner_text())

    # --- scheme card content
    card = page.locator("#scheme-pm_kisan")
    card.locator("summary").first.click() if card.locator("details").first.get_attribute("open") is None else None
    body = card.inner_text().lower()   # headings are CSS-uppercased
    for needle in ("What you get", "₹6,000", "Documents to carry", "Aadhaar", "How to apply", "Open official website"):
        check(f"PM-KISAN card has '{needle}'", needle.lower() in body)
    boxes = card.locator(".docs input[type=checkbox]")
    boxes.first.check()
    check("document checklist counts", "1/" in card.locator("h4", has_text="Documents").inner_text())
    link = card.get_by_role("link", name="Open official website")
    check("apply link is safe", link.get_attribute("rel") == "noopener noreferrer" and link.get_attribute("target") == "_blank" and link.get_attribute("href").startswith("https://"))
    card.get_by_text("Where this comes from").click()
    check("citation shows text and official source", "pmkisan.gov.in" in card.locator(".citations").inner_text() and card.locator(".citations blockquote").count() >= 1)
    page.screenshot(path=f"{SHOTS}/02-scheme-card.png", full_page=True)

    # --- profile editing
    page.get_by_role("button", name="Edit details").click()
    page.locator("#edit-age").fill("70")
    page.locator("#edit-age").blur()
    page.wait_for_function("document.querySelector('.edit-grid') !== null")
    page.wait_for_timeout(600)
    check("edited age is applied", page.locator("#edit-age").input_value() == "70")
    page.get_by_role("button", name="Done").click()
    check("edit shows 70 as set by you", "70" in page.locator(".facts").inner_text())

    # --- ask box
    page.locator("#question").fill("How much money does PM-KISAN give?")
    page.get_by_role("button", name="Ask", exact=True).click()
    page.wait_for_selector(".passages li")
    check("ask returns cited passages", "pmkisan.gov.in" in page.locator(".answer").inner_text())
    page.locator("#question").fill("tell me a joke")
    page.get_by_role("button", name="Ask", exact=True).click()
    page.wait_for_selector("text=We don't have information about that")
    check("off-topic question says 'no information'", True)

    # --- language switching keeps results
    page.get_by_role("button", name="हिन्दी").click()
    page.wait_for_timeout(300)
    check("lang attr switches to hi", page.evaluate("document.documentElement.lang") == "hi")
    check("UI is Hindi", "आपके परिणाम" in page.locator(".results-h").inner_text())
    check("scheme name is Hindi", "पीएम-किसान" in page.locator("#scheme-pm_kisan h3").inner_text())
    page.screenshot(path=f"{SHOTS}/03-hindi.png", full_page=True)
    page.get_by_role("button", name="ಕನ್ನಡ").click()
    page.wait_for_timeout(300)
    check("scheme name is Kannada", "ಪಿಎಂ-ಕಿಸಾನ್" in page.locator("#scheme-pm_kisan h3").inner_text())
    page.wait_for_load_state("networkidle")
    kcard = page.locator("#scheme-pm_kisan")
    if kcard.locator("details").first.get_attribute("open") is None:
        kcard.locator("summary").first.click()
    kcard.locator(".citations summary").click()
    langs = kcard.locator(".citations blockquote").evaluate_all("els => els.map(e => e.lang)")
    check("citations switch to Kannada with the interface", langs and all(l == "kn" for l in langs), str(langs))
    page.screenshot(path=f"{SHOTS}/04-kannada.png", full_page=True)
    stored = page.evaluate("localStorage.getItem('schemesaathi.lang')")
    check("language choice remembered", stored == "kn")

    # --- Kannada input end to end (fresh page, remembered language)
    page.reload()
    check("language restored after reload", page.evaluate("document.documentElement.lang") == "kn")
    page.locator("#situation").fill("ನನಗೆ 34 ವರ್ಷ. ನಾನು ಬೆಂಗಳೂರಿನಲ್ಲಿ ಟೈಲರ್ ಕೆಲಸ ಮಾಡುತ್ತೇನೆ. ನನ್ನ ಮಗಳಿಗೆ 5 ವರ್ಷ. ನನಗೆ ಬ್ಯಾಂಕ್ ಖಾತೆ ಇದೆ.")
    page.get_by_role("button", name="ನನ್ನ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ").click()
    page.wait_for_selector("h2.results-h")
    check("Kannada input: Sukanya shows eligible", "ಅರ್ಹರೆಂದು" in page.locator("#scheme-ssy .badge.status-eligible").inner_text())

    # --- Hindi input
    page.get_by_role("button", name="हिन्दी").click()
    page.locator("#situation").fill("मैं 62 साल का किसान हूं, गांव में रहता हूं। मेरे पास 3 एकड़ जमीन है और बैंक खाता है। महीने में 8000 रुपये कमाता हूं।")
    page.get_by_role("button", name="मेरी योजनाएं खोजें").click()
    page.wait_for_function("document.querySelector('.facts') && document.querySelector('.facts').innerText.includes('96,000')")
    check("Hindi input: monthly income converted to 96,000/yr", True)

    # --- error handling: server down
    page.route("**/api/analyze", lambda r: r.abort())
    page.get_by_role("button", name="मेरी योजनाएं खोजें").click()
    page.wait_for_selector(".banner.error")
    check("network error shown in Hindi", "सर्वर से संपर्क" in page.locator(".banner.error").inner_text())
    page.unroute("**/api/analyze")
    page.route("**/api/analyze", lambda r: r.fulfill(status=429, body="{}"))
    page.get_by_role("button", name="मेरी योजनाएं खोजें").click()
    page.wait_for_selector("text=बहुत ज़्यादा अनुरोध")
    check("429 shows rate-limit message", True)
    page.unroute("**/api/analyze")

    # --- accessibility basics (English)
    page.get_by_role("button", name="English").click()
    page.reload()
    names = page.evaluate("""() => [...document.querySelectorAll('button, a, input, select, textarea')]
        .filter(e => e.offsetParent !== null)
        .filter(e => !(e.getAttribute('aria-label') || e.innerText.trim() || (e.labels && e.labels.length) || e.getAttribute('placeholder')))
        .map(e => e.outerHTML.slice(0, 80))""")
    check("every visible control has an accessible name", names == [], str(names))
    check("skip link exists", page.locator("a.skip").count() == 1)
    ctx.close()

    # --- mobile
    mctx = browser.new_context(viewport={"width": 375, "height": 800}, device_scale_factor=2)
    m = mctx.new_page()
    m.route("**/fonts.g*/**", lambda r: r.abort())
    m.goto(BASE)
    m.get_by_role("button", name="I am a 45 year old farmer woman").click()
    m.get_by_role("button", name="Find my schemes").click()
    m.wait_for_selector("h2.results-h")
    m.wait_for_timeout(400)
    overflow = m.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("mobile: no horizontal scroll", overflow <= 0, f"overflow={overflow}px")
    small = m.evaluate("""() => [...document.querySelectorAll('button, a.btn, input, select')]
        .filter(e => e.offsetParent !== null && !e.closest('.sr-only'))
        .map(e => e.type === 'checkbox' ? e.closest('label') : e)
        .map(e => [e.tagName, (e.innerText||e.getAttribute('aria-label')||'').slice(0,20), Math.round(e.getBoundingClientRect().height)])
        .filter(x => x[2] < 36)""")
    check("mobile: tap targets at least 36px tall", small == [], str(small))
    m.screenshot(path=f"{SHOTS}/05-mobile.png", full_page=True)
    mctx.close()
    browser.close()

fails = [r for r in results if not r[1]]
print(f"\n{len(results) - len(fails)}/{len(results)} checks passed")
print("console errors:", console_errors)
print("page errors:", page_errors)
sys.exit(1 if fails or page_errors else 0)
