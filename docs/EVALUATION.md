# Evaluation

This page explains **how** SchemeSaathi was measured, what the numbers do and do not show, and how to reproduce them. If you quote a number from this project (in an interview, on LinkedIn, on your resume), quote it the way it is written here.

## What was measured

| Component | Question | Script | Data |
|---|---|---|---|
| Profile extractor | From a short description, does it extract the right facts, and does it avoid wrong ones? | `backend/eval/eval_extraction.py` | `extraction_cases.json` (36), `extraction_heldout.json` (18) |
| Retrieval | Does a question find the right scheme, and does an off-topic question return nothing? | `backend/eval/eval_retrieval.py` | `retrieval_cases.json` (27 on-topic + 11 off-topic), `retrieval_heldout.json` (18 + 4) |
| Rule engine, service, API logic | Does it behave as designed? | `pytest` | 172 tests |
| User interface | Does the whole journey work in a browser? | `e2e/e2e.py` | 48 checks |

Cases are split evenly across English, Hindi and Kannada. Every case was written by the project author.

## Metrics

**Extraction** is scored per field. A *wrong* value counts as both a wrong fact and a missed fact, and an unexpected extra fact counts as wrong, because **a wrong fact is worse than a missing one**: a missing fact is simply asked about, while a wrong one silently changes who is told they qualify.

- *precision*: of the facts returned, the share that were right
- *recall*: of the facts actually stated, the share found
- *cases exact*: descriptions where every fact was right and nothing extra was returned

**Retrieval** is scored at the scheme level.

- *hit@1 / hit@3*: the expected scheme is the top result / among the top three
- *MRR*: mean reciprocal rank of the expected scheme (1.0 is perfect)
- *off-topic rejected*: share of off-topic questions (weather, jokes, cricket scores…) that returned **no** passages, which is what lets the app say "we don't have information about that"

## Results

### Extraction

| Set | Cases | Precision | Recall | Cases exact | Notes |
|---|---|---|---|---|---|
| Development, first run | 36 | 97.1% | 96.5% | 30 / 36 | before any extractor fixes |
| Development, final | 36 | 100% | 100% | 36 / 36 | **tuned on this set; optimistic** |
| Second set, **first run** | 18 | **94.4%** | **93.2%** | **14 / 18** | the honest estimate on unseen text |
| Second set, final | 18 | 100% | 100% | 18 / 18 | no longer independent (see below) |

The 4 failing cases on the second set's first run were real bugs, since fixed and covered by regression tests in `tests/test_extract.py`:
a number directly before "daughter" (`8 साल की बेटी`) was read as the speaker's age; "I am her son, 38 years old" lost the speaker's age; and an occupation or government job mentioned for a *relative* was attributed to the speaker (two cases: `पिताजी सरकारी कर्मचारी हैं` and `ನನ್ನ ಪತಿ ಸರ್ಕಾರಿ ನೌಕರ`).
Fixing those exposed one more bug on a re-run (a daughter's age was searched across a sentence boundary), which is also fixed. That is exactly why the second set is no longer independent.

### Retrieval

| Set | On-topic | hit@1 | hit@3 | MRR | Off-topic rejected | Notes |
|---|---|---|---|---|---|---|
| Development, first run | 27 | 92.6% | 96.3% | 0.954 | 0 / 11 | plain character n-gram TF-IDF |
| Development, final | 27 | 100% | 100% | 1.000 | 9 / 11 | after adding a relevance gate and fixing wording; **tuned on this set** |
| Held-out, **first run** | 18 | **83.3%** | **94.4%** | **0.898** | **2 / 4** | not tuned afterwards |

What changed between the first and final development rows: stop-word removal and a "must share a content word" gate (this is what makes off-topic questions return nothing), a hybrid of character and word TF-IDF, and clearer scheme wording where the retriever confused two schemes (for example "health insurance" was missing from the PM-JAY summary).

## How much to trust this

**Be sceptical, for these reasons:**

1. **Small.** 54 extraction cases and 45 on-topic retrieval queries. A single case moves a percentage by 2 to 5 points. Do not read decimals into them.
2. **Same author for the data and the tests.** The scheme text and the test questions came from one person, so the vocabulary overlaps more than it would with real users. Real questions will be messier.
3. **The "held-out" sets are single-use.** I ran each once, fixed what it exposed, and ran it again. The **first-run** rows are the honest estimates; the "final" rows are not independent any more.
4. **Typed text, not speech.** Extraction was evaluated on written descriptions. Speech-to-text errors in Hindi and Kannada will lower real accuracy; this was **not measured**.
5. **Not measured at all:** real users, end-to-end task success, the optional LLM and dense-embedding paths, Whisper accuracy, and whether the Hindi and Kannada wording reads naturally to native speakers.
6. **The weakest number is off-topic rejection (2 of 4 on unseen questions).** Questions that share a word with a scheme ("which stock should I buy" matched a housing passage) can still return a weak hit. The mitigation is built in: `/api/ask` returns `confidence: "low"` and the UI warns *"These may not answer your question"*. A dense embedder with a tuned threshold, evaluated on a larger off-topic set, is the real fix.

## Wording that is accurate

- ✅ "On a small hand-labelled set of 18 unseen descriptions in English, Hindi and Kannada, the extractor's first run scored about 94% precision and 93% recall."
- ✅ "Retrieval put the right scheme in the top 3 for 17 of 18 unseen questions on the first run."
- ✅ "172 automated tests and a 48-check browser test."
- ❌ "99% accurate." (No such measurement exists.)
- ❌ "Works for real users." (It has not been tried with any.)

## Reproduce

```bash
cd backend
pip install -r requirements-dev.txt
python eval/eval_extraction.py          # both extraction sets, with failures listed
python eval/eval_retrieval.py           # both retrieval sets, with misses and leaks listed
python eval/eval_retrieval.py heldout   # one set only (dev | heldout | all)
pytest                                  # 172 tests also enforce accuracy floors on these sets
```

To evaluate the dense embedder: `pip install sentence-transformers` then `EMBEDDING_BACKEND=sentence-transformers python eval/eval_retrieval.py`. Tune `min_score` / `confident_score` in `backend/app/retrieval.py` (or `MIN_RELEVANT_SCORE`) on a **new** set of questions, not on these.

## How to make this evaluation stronger

1. Ask 5 to 10 native Hindi and Kannada speakers to write descriptions in their own words, and **freeze** that set before touching the code.
2. Record real speech and evaluate extraction on the Whisper transcripts.
3. Grow the off-topic set to a few hundred realistic questions (people will ask about things near the topic: tax filing, ration card status, pension amounts).
4. Have a domain expert or caseworker label a sample of "appears to qualify" results as correct or wrong. That is the number that matters most.
