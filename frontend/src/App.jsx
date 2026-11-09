import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import AskBox from "./components/AskBox.jsx";
import Header from "./components/Header.jsx";
import InputCard from "./components/InputCard.jsx";
import ProfilePanel from "./components/ProfilePanel.jsx";
import Questions from "./components/Questions.jsx";
import SchemeCard from "./components/SchemeCard.jsx";
import { AUTHOR_NAME, REPO_URL } from "./config";
import { useStoredState } from "./hooks";
import { t } from "./i18n";

const GROUPS = [
  ["eligible", "groupEligible"],
  ["likely", "groupLikely"],
  ["not_eligible", "groupNot"],
];

export default function App() {
  const [lang, setLang] = useStoredState("schemesaathi.lang", "en");
  const [text, setText] = useState("");
  const [meta, setMeta] = useState(null);
  const [health, setHealth] = useState(null);
  const [result, setResult] = useState(null);
  const [analyzedText, setAnalyzedText] = useState("");
  const [overrides, setOverrides] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const latest = useRef(0);
  const controller = useRef(null);
  const heading = useRef(null);
  const focusResults = useRef(false);
  const langRef = useRef(lang);
  langRef.current = lang;

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    const abort = new AbortController();
    Promise.all([api.meta(abort.signal), api.health(abort.signal)])
      .then(([m, h]) => {
        setMeta(m);
        setHealth(h);
      })
      .catch((err) => err.name !== "AbortError" && setError(err.kind || "server"));
    return () => abort.abort();
  }, []);

  useEffect(() => {
    if (analyzedText || Object.keys(overrides).length) run(analyzedText, overrides);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  // Move keyboard / screen-reader focus to the results after a NEW search (not after small edits).
  useEffect(() => {
    if (result && focusResults.current) {
      focusResults.current = false;
      heading.current?.focus();
    }
  }, [result]);

  const run = useCallback(async (sourceText, nextOverrides, { focus } = {}) => {
    controller.current?.abort();
    controller.current = new AbortController();
    const mine = ++latest.current;
    setLoading(true);
    setError(null);
    try {
      const data = await api.analyze({ text: sourceText, overrides: nextOverrides, lang: langRef.current }, controller.current.signal);
      if (mine !== latest.current) return; // a newer request replaced this one
      focusResults.current = !!focus;
      setResult(data);
      setAnalyzedText(sourceText);
    } catch (err) {
      if (err.name === "AbortError" || mine !== latest.current) return;
      setError(err.kind || "server");
    } finally {
      if (mine === latest.current) setLoading(false);
    }
  }, []);

  const submit = () => {
    if (!text.trim()) return;
    setOverrides({});
    run(text, {}, { focus: true });
  };

  const applyOverride = (field, value) => {
    const next = { ...overrides, [field]: value };
    setOverrides(next);
    run(analyzedText, next);
  };

  const errorText = (kind) => t(lang, kind === "network" ? "errorNetwork" : kind === "rate" ? "errorRate" : "errorGeneric");
  const warnings = (result?.warnings || []).map((w) => (w === "income_daily" ? "warnIncomeDaily" : "warnIncomeUnclear"));
  const byStatus = (status) => (result?.results || []).filter((r) => r.status === status);

  return (
    <>
      <a className="skip" href="#results">{t(lang, "skip")}</a>
      <Header lang={lang} onLang={setLang} />
      <main>
        <section className="hero">
          <h1 lang={lang}>{t(lang, "heroTitle")}</h1>
          <p lang={lang}>{t(lang, "heroSub")}</p>
        </section>

        <InputCard lang={lang} text={text} onText={setText} onSubmit={submit} loading={loading} transcriptionAvailable={!!health?.transcription} />

        {error && <p className="banner error" role="alert">{errorText(error)}</p>}

        <div id="results" aria-live="polite">
          {result && meta && (
            <>
              <h2 className="results-h" tabIndex={-1} ref={heading}>{t(lang, "resultsHeading")}</h2>
              {!result.data_verified && <p className="banner warn" role="note">{t(lang, "dataBanner")}</p>}

              <ul className="summary-chips" aria-label={t(lang, "resultsHeading")}>
                <li className="status-eligible"><strong>{result.counts.eligible}</strong> {t(lang, "summaryEligible")}</li>
                <li className="status-likely"><strong>{result.counts.likely}</strong> {t(lang, "summaryLikely")}</li>
                <li className="status-not_eligible"><strong>{result.counts.not_eligible}</strong> {t(lang, "summaryNot")}</li>
              </ul>

              <ProfilePanel lang={lang} meta={meta} profile={result.profile} sources={result.field_sources} onChange={applyOverride} />

              {warnings.map((key) => (
                <p className="banner warn" role="note" key={key}>{t(lang, key)}</p>
              ))}

              <Questions lang={lang} meta={meta} fields={result.next_questions} onAnswer={applyOverride} />

              {GROUPS.map(([status, label]) => {
                const items = byStatus(status);
                if (!items.length) return null;
                const list = items.map((scheme, i) => <SchemeCard key={scheme.id} lang={lang} scheme={scheme} defaultOpen={status === "eligible" && i === 0} />);
                return status === "not_eligible" ? (
                  <details className="group group-closed" key={status}>
                    <summary>{t(lang, label)} ({items.length})</summary>
                    {list}
                  </details>
                ) : (
                  <section className="group" key={status} aria-label={t(lang, label)}>
                    <h2>{t(lang, label)} <span className="count">{items.length}</span></h2>
                    {list}
                  </section>
                );
              })}

              <p className="disclaimer" lang={lang}>{t(lang, "disclaimer")}</p>
            </>
          )}
        </div>

        <AskBox lang={lang} errorText={errorText} />
      </main>

      <footer>
        <p>
          {t(lang, "footerBuiltBy")} <a href={REPO_URL} target="_blank" rel="noopener noreferrer">{AUTHOR_NAME}</a> · {t(lang, "footerNote")}
        </p>
      </footer>
    </>
  );
}
