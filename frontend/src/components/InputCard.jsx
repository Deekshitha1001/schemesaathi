import { t } from "../i18n";
import { useVoice } from "../hooks";

export default function InputCard({ lang, text, onText, onSubmit, loading, transcriptionAvailable }) {
  const voice = useVoice({
    lang,
    serverAvailable: transcriptionAvailable,
    onText: (spoken) => onText((prev) => (prev.trim() ? `${prev.trim()} ${spoken}` : spoken)),
  });
  const examples = t(lang, "examples");
  const micLabel = voice.status === "listening" ? t(lang, "micStop") : t(lang, "mic");
  const voiceMessage =
    voice.error === "denied" ? t(lang, "voiceDenied") : voice.error === "unsupported" ? t(lang, "voiceUnsupported") : voice.error ? t(lang, "voiceError") : null;

  return (
    <form
      className="card input-card"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <label htmlFor="situation" className="field-label">
        {t(lang, "inputLabel")}
      </label>
      <textarea
        id="situation"
        lang={lang}
        rows={5}
        maxLength={2000}
        value={text}
        placeholder={t(lang, "placeholder")}
        onChange={(e) => onText(e.target.value)}
        onKeyDown={(e) => {
          if ((e.ctrlKey || e.metaKey) && e.key === "Enter") onSubmit();
        }}
      />
      <div className="actions">
        <button type="button" className={`btn mic ${voice.status === "listening" ? "recording" : ""}`} onClick={voice.toggle} disabled={voice.status === "transcribing"} aria-pressed={voice.status === "listening"}>
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
            <path fill="currentColor" d="M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V22h2v-3.08A7 7 0 0 0 19 12h-2z" />
          </svg>
          {micLabel}
        </button>
        <button type="submit" className="btn primary" disabled={loading || !text.trim()}>
          {loading ? t(lang, "finding") : t(lang, "find")}
        </button>
      </div>
      <p className="status" role="status" aria-live="polite">
        {voice.status === "listening" && t(lang, "listening")}
        {voice.status === "transcribing" && t(lang, "transcribing")}
        {voiceMessage && <span className="error-text">{voiceMessage}</span>}
      </p>
      <div className="examples">
        <span>{t(lang, "tryExample")}</span>
        {examples.map((example, i) => (
          <button key={i} type="button" className="chip" lang={lang} onClick={() => onText(example)}>
            {example.length > 46 ? `${example.slice(0, 44)}…` : example}
          </button>
        ))}
      </div>
      <p className="muted small">{t(lang, "privacy")}</p>
    </form>
  );
}
