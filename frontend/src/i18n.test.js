// Run with:  npm test   (Node's built-in test runner, no dependencies)
import test from "node:test";
import assert from "node:assert/strict";
import { LANGS, UI, t } from "./i18n.js";

const codes = LANGS.map((l) => l.code);

test("every UI string exists in every language", () => {
  const reference = Object.keys(UI.en);
  for (const code of codes) {
    const missing = reference.filter((key) => !(key in UI[code]));
    const extra = Object.keys(UI[code]).filter((key) => !(key in UI.en));
    assert.deepEqual(missing, [], `${code} is missing keys`);
    assert.deepEqual(extra, [], `${code} has keys English lacks`);
  }
});

test("no string is empty and examples are non-empty lists", () => {
  for (const code of codes) {
    for (const [key, value] of Object.entries(UI[code])) {
      if (Array.isArray(value)) {
        assert.ok(value.length >= 3 && value.every((v) => v.trim()), `${code}.${key}`);
      } else {
        assert.ok(String(value).trim(), `${code}.${key} is empty`);
      }
    }
  }
});

test("Hindi and Kannada are really translated, not copies of English", () => {
  const sameAsEnglish = (code) => Object.keys(UI.en).filter((k) => typeof UI.en[k] === "string" && UI.en[k].length > 12 && UI[code][k] === UI.en[k]);
  assert.deepEqual(sameAsEnglish("hi"), []);
  assert.deepEqual(sameAsEnglish("kn"), []);
});

test("t() falls back to English, then to the key", () => {
  assert.equal(t("xx", "find"), UI.en.find);
  assert.equal(t("en", "no_such_key"), "no_such_key");
});
