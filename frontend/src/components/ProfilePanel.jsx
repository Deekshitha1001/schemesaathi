import { useState } from "react";
import { displayValue } from "../fields";
import { t } from "../i18n";

const SOURCE_KEY = { rules: "srcRules", llm: "srcLlm", user: "srcUser" };

function FieldEditor({ spec, field, value, lang, meta, onChange }) {
  const id = `edit-${field}`;
  if (spec.type === "number") {
    return (
      <input
        id={id}
        type="number"
        inputMode="numeric"
        min="0"
        defaultValue={value ?? ""}
        key={String(value)}
        onBlur={(e) => {
          const next = e.target.value === "" ? null : Number(e.target.value);
          if (next !== (value ?? null)) onChange(field, next);
        }}
        onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
      />
    );
  }
  const options =
    spec.type === "bool"
      ? [["true", meta.yes_no.true[lang]], ["false", meta.yes_no.false[lang]]]
      : Object.entries(spec.options).map(([k, v]) => [k, v[lang]]);
  const current = value === undefined ? "" : String(value);
  return (
    <select
      id={id}
      value={current}
      onChange={(e) => {
        const v = e.target.value;
        onChange(field, v === "" ? null : spec.type === "bool" ? v === "true" : v);
      }}
    >
      <option value="">{t(lang, "unknown")}</option>
      {options.map(([k, label]) => (
        <option key={k} value={k}>
          {label}
        </option>
      ))}
    </select>
  );
}

export default function ProfilePanel({ lang, meta, profile, sources, onChange }) {
  const [editing, setEditing] = useState(false);
  const known = meta.order.filter((f) => profile[f] !== undefined);

  return (
    <section className="card" aria-labelledby="understood-h">
      <div className="card-head">
        <h2 id="understood-h">{t(lang, "understood")}</h2>
        <button type="button" className="btn small" onClick={() => setEditing((v) => !v)} aria-expanded={editing}>
          {editing ? t(lang, "done") : t(lang, "edit")}
        </button>
      </div>

      {!editing && (known.length ? (
        <ul className="facts">
          {known.map((field) => (
            <li key={field} title={t(lang, SOURCE_KEY[sources[field]] || "srcRules")}>
              <span className="fact-label">{meta.fields[field].label[lang]}</span>
              <strong>{displayValue(meta, field, profile[field], lang)}</strong>
              <span className={`src src-${sources[field] || "rules"}`}>{t(lang, SOURCE_KEY[sources[field]] || "srcRules")}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">{t(lang, "nothingUnderstood")}</p>
      ))}

      {editing && (
        <div className="edit-grid">
          {meta.order.map((field) => (
            <div className="edit-row" key={field}>
              <label htmlFor={`edit-${field}`}>{meta.fields[field].label[lang]}</label>
              <FieldEditor spec={meta.fields[field]} field={field} value={profile[field]} lang={lang} meta={meta} onChange={onChange} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
