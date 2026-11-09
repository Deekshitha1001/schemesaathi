// Thin client for the FastAPI backend. All errors are turned into ApiError(kind) so the UI can show a translated message.

const BASE = (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_BASE) || "";

export class ApiError extends Error {
  constructor(kind, status = 0) {
    super(kind);
    this.kind = kind; // "network" | "rate" | "unavailable" | "server"
    this.status = status;
  }
}

async function request(path, { method = "GET", json, form, signal } = {}) {
  let response;
  try {
    response = await fetch(BASE + path, {
      method,
      signal,
      headers: json ? { "Content-Type": "application/json" } : undefined,
      body: json ? JSON.stringify(json) : form,
    });
  } catch (err) {
    if (err && err.name === "AbortError") throw err;
    throw new ApiError("network");
  }
  if (!response.ok) {
    throw new ApiError(response.status === 429 ? "rate" : response.status === 501 ? "unavailable" : "server", response.status);
  }
  return response.json();
}

export const api = {
  health: (signal) => request("/api/health", { signal }),
  meta: (signal) => request("/api/meta", { signal }),
  analyze: ({ text, overrides, lang }, signal) => request("/api/analyze", { method: "POST", json: { text, overrides, lang }, signal }),
  ask: ({ question, lang }, signal) => request("/api/ask", { method: "POST", json: { question, lang }, signal }),
  transcribe: (blob, lang, signal) => {
    const form = new FormData();
    form.append("audio", blob, "speech.webm");
    form.append("lang", lang);
    return request("/api/transcribe", { method: "POST", form, signal });
  },
};
