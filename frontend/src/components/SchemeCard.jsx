import { useEffect, useState } from "react";
import { levelLabel } from "../fields";
import { t } from "../i18n";

const CHECK = { pass: ["✓", "checkPass"], soft: ["≈", "checkSoft"], unknown: ["?", "checkUnknown"], fail: ["✗", "checkFail"] };
const STATUS = { eligible: "statusEligible", likely: "statusLikely", not_eligible: "statusNot" };

function Citations({ lang, citations }) {
  if (!citations.length) return null;
  return (
    <details className="citations">
      <summary>{t(lang, "whereFrom")} ({citations.length})</summary>
      <ol>
        {citations.map((c) => (
          <li key={c.id}>
            <p className="cite-kind">{c.origin === "ingested" ? t(lang, "officialDoc") : t(lang, "summaryOf")}</p>
            <blockquote lang={c.lang}>{c.text}</blockquote>
            <a href={c.source_url} target="_blank" rel="noopener noreferrer">
              {t(lang, "source")}: {new URL(c.source_url).hostname}
            </a>
          </li>
        ))}
      </ol>
    </details>
  );
}

export default function SchemeCard({ lang, scheme, defaultOpen }) {
  const [checked, setChecked] = useState({});
  const ready = scheme.documents.filter((d) => checked[d.id]).length;
  const name = scheme.name[lang];
  const unknownLeft = scheme.checks.filter((c) => c.result === "unknown");

  useEffect(() => setChecked({}), [scheme.id]);

  const share = () => {
    const message = `${t(lang, "whatsappText")}: ${name}\n${scheme.benefit[lang]}\n${scheme.apply_url}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, "_blank", "noopener,noreferrer");
  };
  const print = () => {
    const card = document.getElementById(`scheme-${scheme.id}`);
    document.body.classList.add("printing-one");
    card.classList.add("print-target");
    const cleanup = () => {
      document.body.classList.remove("printing-one");
      card.classList.remove("print-target");
      window.removeEventListener("afterprint", cleanup);
    };
    window.addEventListener("afterprint", cleanup);
    window.print();
  };

  return (
    <article className={`card scheme status-${scheme.status}`} id={`scheme-${scheme.id}`} aria-labelledby={`h-${scheme.id}`}>
      <details open={defaultOpen}>
        <summary>
          <span className="summary-main">
            <h3 id={`h-${scheme.id}`} lang={lang}>{name}</h3>
            <span className="badges">
              <span className={`badge status-${scheme.status}`}>{t(lang, STATUS[scheme.status])}</span>
              <span className="badge level">{levelLabel(scheme.level, lang)}</span>
            </span>
          </span>
          <span className="summary-sub" lang={lang}>{scheme.summary[lang]}</span>
        </summary>

        <div className="scheme-body" lang={lang}>
          <section>
            <h4>{t(lang, "benefit")}</h4>
            <p className="benefit">{scheme.benefit[lang]}</p>
          </section>

          <section>
            <h4>{t(lang, "requirements")}</h4>
            <ul className="checks">
              {scheme.checks.map((c, i) => {
                const [icon, label] = CHECK[c.result];
                return (
                  <li key={i} className={`check-${c.result}`}>
                    <span className="check-icon" aria-hidden="true">{icon}</span>
                    <span className="sr-only">{t(lang, label)}: </span>
                    <span>{c.text[lang]}</span>
                    {c.result !== "pass" && <em className="check-label"> — {t(lang, label)}</em>}
                  </li>
                );
              })}
            </ul>
            {scheme.status === "likely" && unknownLeft.length > 0 && <p className="muted small">{t(lang, "needToConfirm")}: {unknownLeft.length}</p>}
          </section>

          {scheme.status !== "not_eligible" && (
            <>
              <section>
                <h4>
                  {t(lang, "documents")} <span className="muted small">({ready}/{scheme.documents.length} {t(lang, "docsReady")})</span>
                </h4>
                <ul className="docs">
                  {scheme.documents.map((d) => (
                    <li key={d.id}>
                      <label>
                        <input type="checkbox" checked={!!checked[d.id]} onChange={(e) => setChecked((prev) => ({ ...prev, [d.id]: e.target.checked }))} />
                        <span>{d.text[lang]}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </section>

              <section>
                <h4>{t(lang, "howToApply")}</h4>
                <p>{scheme.how_to_apply[lang]}</p>
                <div className="actions">
                  <a className="btn primary" href={scheme.apply_url} target="_blank" rel="noopener noreferrer">{t(lang, "openSite")} ↗</a>
                  <button type="button" className="btn" onClick={share}>{t(lang, "share")}</button>
                  <button type="button" className="btn" onClick={print}>{t(lang, "print")}</button>
                </div>
              </section>

              <Citations lang={lang} citations={scheme.citations} />
            </>
          )}
        </div>
      </details>
    </article>
  );
}
