import { formatNumber, t } from "./i18n";

/** Human-readable value of a profile field in the chosen UI language. */
export function displayValue(meta, field, value, lang) {
  const spec = meta.fields[field];
  if (!spec) return String(value);
  if (spec.type === "bool") return meta.yes_no[value ? "true" : "false"][lang];
  if (spec.type === "enum") return spec.options[value]?.[lang] ?? String(value);
  if (field === "annual_income") return `${t(lang, "rupee")}${formatNumber(value)}`;
  return formatNumber(value);
}

/** Language-specific name for a scheme-level badge. */
export const levelLabel = (level, lang) => t(lang, level === "karnataka" ? "karnataka" : "central");
