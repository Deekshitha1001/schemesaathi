import { t } from "../i18n";

function Answer({ spec, field, lang, meta, onAnswer }) {
  if (spec.type === "number") {
    return (
      <input
        type="number"
        inputMode="numeric"
        min="0"
        aria-label={spec.label[lang]}
        onKeyDown={(e) => {
          if (e.key === "Enter" && e.currentTarget.value !== "") onAnswer(field, Number(e.currentTarget.value));
        }}
        onBlur={(e) => e.target.value !== "" && onAnswer(field, Number(e.target.value))}
      />
    );
  }
  const options =
    spec.type === "bool"
      ? [[true, meta.yes_no.true[lang]], [false, meta.yes_no.false[lang]]]
      : Object.entries(spec.options).map(([k, v]) => [k, v[lang]]);
  return (
    <div className="answers" role="group" aria-label={spec.label[lang]}>
      {options.map(([value, label]) => (
        <button key={String(value)} type="button" className="chip choice" onClick={() => onAnswer(field, value)}>
          {label}
        </button>
      ))}
    </div>
  );
}

const MAX_QUESTIONS = 4; // asking everything at once overwhelms people; the next ones appear as these are answered

export default function Questions({ lang, meta, fields: allFields, onAnswer }) {
  const fields = allFields.slice(0, MAX_QUESTIONS);
  if (!fields.length) return null;
  return (
    <section className="card questions" aria-labelledby="help-h">
      <h2 id="help-h">{t(lang, "help")}</h2>
      <p className="muted">{t(lang, "helpSub")}</p>
      <ul>
        {fields.map((field) => (
          <li key={field}>
            <p lang={lang}>{meta.fields[field].question[lang]}</p>
            <Answer spec={meta.fields[field]} field={field} lang={lang} meta={meta} onAnswer={onAnswer} />
          </li>
        ))}
      </ul>
    </section>
  );
}
