import { LANGS, t } from "../i18n";

export default function Header({ lang, onLang }) {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <a className="brand" href="/" aria-label="SchemeSaathi">
          <svg viewBox="0 0 64 64" width="36" height="36" aria-hidden="true">
            <rect width="64" height="64" rx="14" fill="currentColor" />
            <path d="M20 34l9 9 17-20" fill="none" stroke="#f3b64c" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>
            <strong>SchemeSaathi</strong>
            <small>{t(lang, "tagline")}</small>
          </span>
        </a>
        <div className="lang-switch" role="group" aria-label={t(lang, "languageLabel")}>
          {LANGS.map((l) => (
            <button key={l.code} type="button" lang={l.code} aria-pressed={lang === l.code} className={lang === l.code ? "on" : ""} onClick={() => onLang(l.code)}>
              {l.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}
