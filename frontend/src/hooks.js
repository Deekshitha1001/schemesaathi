import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { LANGS } from "./i18n";

const SpeechRecognitionImpl = typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;

/** localStorage that never throws (private windows, blocked storage). */
export function useStoredState(key, initial) {
  const [value, setValue] = useState(() => {
    try {
      return window.localStorage.getItem(key) ?? initial;
    } catch {
      return initial;
    }
  });
  const set = useCallback(
    (next) => {
      setValue(next);
      try {
        window.localStorage.setItem(key, next);
      } catch {
        /* storage unavailable: the choice just won't be remembered */
      }
    },
    [key]
  );
  return [value, set];
}

/**
 * Voice input with two engines:
 *  - "server":  record with MediaRecorder and send to /api/transcribe (Whisper). Used when the backend reports it is installed.
 *  - "browser": the browser's SpeechRecognition (Chrome/Edge/Safari). No server needed, but audio goes to the browser vendor's service.
 * `onText(text)` receives the final transcript.
 */
export function useVoice({ lang, serverAvailable, onText }) {
  const [status, setStatus] = useState("idle"); // idle | listening | transcribing
  const [error, setError] = useState(null); // unsupported | denied | failed
  const recognizer = useRef(null);
  const recorder = useRef(null);
  const onTextRef = useRef(onText);
  onTextRef.current = onText;

  const hasMedia = typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";
  const engine = serverAvailable && hasMedia ? "server" : SpeechRecognitionImpl ? "browser" : null;

  const stop = useCallback(() => {
    recognizer.current?.stop();
    if (recorder.current && recorder.current.state !== "inactive") recorder.current.stop();
  }, []);

  useEffect(() => () => {
    recognizer.current?.abort?.();
    if (recorder.current && recorder.current.state !== "inactive") recorder.current.stop();
  }, []);

  const startBrowser = useCallback(() => {
    const recognition = new SpeechRecognitionImpl();
    recognition.lang = LANGS.find((l) => l.code === lang)?.speech || "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    let transcript = "";
    recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) transcript += " " + event.results[i][0].transcript;
      }
    };
    recognition.onerror = (event) => setError(event.error === "not-allowed" || event.error === "service-not-allowed" ? "denied" : event.error === "no-speech" ? "failed" : "failed");
    recognition.onend = () => {
      setStatus("idle");
      if (transcript.trim()) onTextRef.current(transcript.trim());
    };
    recognizer.current = recognition;
    setStatus("listening");
    recognition.start();
  }, [lang]);

  const startServer = useCallback(async () => {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("denied");
      return;
    }
    const chunks = [];
    const mr = new MediaRecorder(stream);
    mr.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    mr.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      setStatus("transcribing");
      try {
        const result = await api.transcribe(new Blob(chunks, { type: mr.mimeType || "audio/webm" }), lang);
        if (result.text) onTextRef.current(result.text);
        else setError("failed");
      } catch {
        setError("failed");
      } finally {
        setStatus("idle");
      }
    };
    recorder.current = mr;
    mr.start();
    setStatus("listening");
  }, [lang]);

  const toggle = useCallback(() => {
    setError(null);
    if (status === "listening") return stop();
    if (status !== "idle") return;
    if (!engine) return setError("unsupported");
    return engine === "server" ? startServer() : startBrowser();
  }, [status, engine, stop, startServer, startBrowser]);

  return { status, error, supported: !!engine, engine, toggle };
}
