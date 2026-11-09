# Resume, LinkedIn post and demo video

Everything below is worded to match what was actually built and measured. If you change a claim, change it only to something you can show or explain in an interview.

## ✅ Before you post anything (do these first, in order)

1. **Run the real stack once.** `pytest` and `python e2e/e2e.py` (see README). The FastAPI layer (`backend/app/main.py`) and Vite build were never executed while this was built, so expect to fix small things. This is normal and also a good interview story.
2. **Verify the scheme data** against official sources with `docs/DATA_VERIFICATION.md`, then `python scripts/mark_verified.py …`. Until all 12 schemes are verified the app shows a "demo data" banner. **Do not post a public demo that tells real people wrong amounts or rules.**
3. **Try the voice input yourself** in Chrome, in Kannada and Hindi. It could not be tested here (no microphone). If it does not work well for a language, say so in the video rather than showing it.
4. **Ask a native speaker** to read the Hindi and Kannada text (`frontend/src/i18n.js`, `backend/data/schemes.json`, `documents.json`, `app/fields.py`). Fix their corrections.
5. **Put your repo link in** `frontend/src/config.js` (`REPO_URL`) and in the post.
6. **Deploy** (optional but strong): a free tier host for the backend and a static host for the frontend; set `CORS_ORIGINS` or use the Docker setup. Put the live link in the post.
7. **Re-read the claims below** and delete any you cannot back up.

## Resume: project entry

Pick 3 to 5 bullets. Keep the numbers exactly as written.

**SchemeSaathi — multilingual welfare-scheme finder** · Python, FastAPI, React, scikit-learn, Whisper, Playwright · [GitHub link] · [live demo link]

- Built a full-stack assistant (FastAPI + React) that reads a person's situation in **English, Hindi or Kannada**, typed or spoken, and matches them to **12 central and Karnataka welfare schemes** with the documents to carry, where to apply, and a **cited source** for each result.
- Designed a **deterministic, three-valued eligibility engine** (pass / unknown / fail) so missing information produces a follow-up question instead of a wrong "not eligible"; the LLM is used only to read the description and **never decides eligibility**, and its output is validated field by field.
- Implemented **retrieval with citations** (hybrid character + word TF-IDF index, stop-word handling, relevance gating) so off-topic questions return "no information" rather than a guess; added an ingestion pipeline for official PDFs.
- Wrote a rule-based multilingual extractor (Devanagari and Kannada digits, lakh/monthly-to-yearly income, negation, facts about relatives) and **evaluated it on hand-labelled sets**: first run on 18 unseen descriptions scored about **94% precision / 93% recall**; documented the held-out methodology and its limits.
- Shipped **172 automated tests** and a **48-check Playwright browser test** (three languages, error states, mobile layout, accessible names), plus Docker files and a generated data-verification checklist.
- Built with privacy in mind: no storage or logging of user input; uploaded audio deleted immediately (tested, including on failure); per-client rate limiting.

One-line version for a tight resume: *Built SchemeSaathi, a full-stack (FastAPI, React) multilingual assistant that matches people to 12 welfare schemes from spoken or typed descriptions in English, Hindi and Kannada, with a rule-based eligibility engine, cited sources and 170+ tests.*

**Skills to add to your skills section if they are now true for you:** FastAPI, REST API design, Docker, Playwright / end-to-end testing, information retrieval (TF-IDF), prompt/LLM output validation, internationalisation (Hindi, Kannada), pytest.

**Your existing summary line could become:** *Recent AI & Data Science graduate who builds end-to-end AI products: from retrieval and speech to a tested, multilingual full-stack application.*

## LinkedIn post (about 200 words)

> Millions of eligible people miss out on government benefits. Not because the schemes don't exist, but because finding them means reading dense rules, often in a language they don't use.
>
> So I built **SchemeSaathi**. Describe your situation in English, Hindi or Kannada, typed or spoken, and it shows which central and Karnataka schemes you may qualify for, the documents to carry, where to apply, and the source behind every answer.
>
> Three design choices I care about:
> 🔹 **The LLM never decides eligibility.** Plain, tested rules do, so every answer can be explained line by line.
> 🔹 **"I don't know" is a valid answer.** Missing information triggers a follow-up question, never a wrong "you're not eligible". Off-topic questions get "we have no information", not a guess.
> 🔹 **Everything is cited.**
>
> Under the hood: FastAPI, React, retrieval with citations, optional Whisper speech-to-text, 170+ tests, and a hand-labelled evaluation set. The README shows the results *including where it fails*.
>
> It's a portfolio project, not an official service. I'd love feedback from native Hindi and Kannada speakers on the wording.
>
> 🎥 Demo in the video · 💻 Code: [link]
>
> #AI #DataScience #FastAPI #React #NLP #OpenToWork #GovTech

Tips: post the video natively (not a link); put the repo link in the first comment if you want more reach; reply to every comment in the first hour. Keep "#OpenToWork" only if it matches how you want to be seen. Remove "optional Whisper speech-to-text" if you have not tried it.

## Demo video script (about 80 seconds)

Record the screen at 1080p. Use a **fictional person**, never real data. Add English captions, since many viewers watch muted. For LinkedIn a square or 4:5 crop of the app works well; the app is responsive, so a narrow browser window also looks good.

| Time | Show | Say / caption |
|---|---|---|
| 0:00–0:07 | Big text on screen: *"Millions miss benefits they qualify for."* then the empty app | "Many people miss government benefits because finding them is hard. So I built SchemeSaathi." |
| 0:07–0:25 | Speak (or type) in **Kannada**: age 34, tailor in Bengaluru, daughter aged 5, has a bank account. The "What we understood" card fills in. | "I describe my situation in my own language. It understands age, work, my daughter and my bank account." |
| 0:25–0:40 | Results appear; scroll through *appears to qualify* / *may qualify*. Open one card: benefit, ticks next to requirements. | "It checks the rules and shows what I may qualify for, and exactly which requirement is met." |
| 0:40–0:52 | Tick off the documents; click *Open official website*. | "I get a checklist of documents to carry and where to apply." |
| 0:52–1:02 | Answer a follow-up ("Do you pay income tax?" → No). A scheme flips from *may qualify* to *appears to qualify*. | "When it isn't sure, it asks, instead of guessing." |
| 1:02–1:12 | Open *Where this comes from*. Then ask "tell me a joke" → *"We don't have information about that."* | "Every answer cites a source. And if it doesn't know, it says so." |
| 1:12–1:20 | Slide or README diagram: *rules decide, the LLM only reads*. Test count on screen. | "The LLM never decides eligibility. Tested rules do. 170+ tests, and an evaluation set with honest results." |
| 1:20–1:25 | Repo link and your name | "Code is open source. Feedback from Hindi and Kannada speakers is very welcome." |

**Do not show:** the "demo data" banner as if the data were verified. Either finish verification first, or open with one sentence saying the scheme data is still being verified.

## Interview questions this project prepares you for (and honest answers)

**Why not let the LLM decide who is eligible?**
Eligibility is a yes/no question about published criteria. An LLM can sound sure and be wrong, and a wrong "you qualify" or "you don't" costs a real person real money. Rules in code can be explained line by line and unit-tested. The LLM's job is only to read messy language into known fields, and even that output is validated.

**What happens when the user doesn't give enough information?**
Each requirement is *pass, unknown or fail*. Only a contradiction makes someone "not eligible". Unknowns produce "may qualify" and a follow-up question, chosen to settle as many schemes as possible. A test asserts that an empty profile is never "not eligible" for any scheme.

**How did you evaluate it? How good is it really?**
Hand-labelled sets in three languages. On 18 unseen descriptions the extractor's first run was about 94% precision and 93% recall. Retrieval found the right scheme in the top 3 for 17 of 18 unseen questions. The weakest part is rejecting off-topic questions (2 of 4 unseen), so the UI shows a "weak match" warning. The sets are small and written by me, so I treat the numbers as sanity checks, and I list what I did not measure: real users and speech errors.

**What bugs did the evaluation find?**
For example, "my daughter is 8 years old" being read as the speaker's age, and "my father is a government employee" being applied to the speaker. I fixed each and added a regression test.

**What would you do next?**
Verify the data and ingest the official documents, evaluate with native speakers and real speech, switch to dense multilingual embeddings tuned on a larger set, move the in-memory index and rate limiter to shared stores, and test with actual users.

**What doesn't work or isn't finished?**
Be direct: scheme data needs verification, the Hindi and Kannada text needs native review, voice input and the Whisper path were not tested end to end, and eligibility is indicative because some criteria depend on government lists the app cannot see. Saying this clearly is a strength in an interview, not a weakness.
