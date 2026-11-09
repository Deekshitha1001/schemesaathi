import { useRef, useState } from "react";
import { api } from "../api";
import { t } from "../i18n";

export default function AskBox({ lang, errorText }) {
  const [question, setQuestion] = useState("");
  const [state, setState] = useState({ loading: false, data: null, error: null });
  const counter = useRef(0);

  const submit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    const mine = ++counter.current;
    setState({ loading: true, data: null, error: null });
    try {
      const data = await api.ask({ question, lang });
      if (mine === counter.current) setState({ loading: false, data, error: null });
    } catch (err) {
      if (mine === counter.current) setState({ loading: false, data: null, error: err.kind || "server" });
    }
  };

  const { data } = state;
  return (
    <section className="card ask" aria-labelledby="ask-h">
      <h2 id="ask-h">{t(lang, "askTitle")}</h2>
      <form className="ask-form" onSubmit={submit}>
        <label htmlFor="question" className="sr-only">{t(lang, "askTitle")}</label>
        <input id="question" type="text" lang={lang} maxLength={500} value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={t(lang, "askPlaceholder")} />
        <button className="btn primary" type="submit" disabled={state.loading || !question.trim()}>{state.loading ? t(lang, "asking") : t(lang, "ask")}</button>
      </form>

      <div role="status" aria-live="polite">
        {state.error && <p className="error-text">{errorText(state.error)}</p>}
        {data && !data.grounded && <p className="muted">{t(lang, "noInfo")}</p>}
        {data && data.grounded && (
          <div className="answer">
            {data.confidence === "low" && <p className="warn">{t(lang, "weakMatch")}</p>}
            {data.answer && (
              <>
                <h3>{t(lang, "answer")}</h3>
                <p lang={data.lang}>{data.answer}</p>
              </>
            )}
            <h3>{t(lang, "closest")}</h3>
            <ol className="passages">
              {data.passages.map((p) => (
                <li key={p.id}>
                  <blockquote lang={p.lang}>{p.text}</blockquote>
                  <a href={p.source_url} target="_blank" rel="noopener noreferrer">{t(lang, "source")}: {new URL(p.source_url).hostname}</a>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </section>
  );
}
