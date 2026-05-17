import { useEffect, useRef, useCallback, useState } from "react";

export type WakeWordStatus = "idle" | "listening" | "detected";

interface UseWakeWordOptions {
  phrases: string[]; // kept for API compat, ignored — hardcoded to full phrase
  onDetected: () => void;
  enabled?: boolean;
}

export function useWakeWord({ onDetected, enabled = true }: UseWakeWordOptions) {
  const [status, setStatus] = useState<WakeWordStatus>("idle");
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const restartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activeRef = useRef(false);
  const firedRef = useRef(false); // prevent double-fire within one session

  const normalize = (s: string) =>
    s
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, "")
      .trim();

  // Must contain BOTH "hey alfred" AND "batman speaking" in the same utterance
  const isFullPhrase = useCallback((transcript: string) => {
    const t = normalize(transcript);
    return t.includes("hey alfred") && t.includes("batman speaking");
  }, []);

  const start = useCallback(() => {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!SR) return;

    try {
      recognitionRef.current?.stop();
    } catch {}

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognitionRef.current = recognition;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      if (firedRef.current) return;
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (isFullPhrase(transcript)) {
          firedRef.current = true;
          setStatus("detected");
          onDetected();
          return;
        }
      }
    };

    recognition.onend = () => {
      if (activeRef.current) {
        restartTimerRef.current = setTimeout(() => {
          if (activeRef.current) {
            firedRef.current = false; // reset for next utterance
            try {
              recognitionRef.current?.start();
            } catch {}
          }
        }, 300);
      }
    };

    recognition.onerror = (e) => {
      if (e.error === "not-allowed") {
        setStatus("idle");
        activeRef.current = false;
      }
    };

    try {
      recognition.start();
      setStatus("listening");
    } catch {}
  }, [isFullPhrase, onDetected]);

  const stop = useCallback(() => {
    activeRef.current = false;
    firedRef.current = false;
    if (restartTimerRef.current) clearTimeout(restartTimerRef.current);
    try {
      recognitionRef.current?.stop();
    } catch {}
    setStatus("idle");
  }, []);

  useEffect(() => {
    if (enabled) {
      activeRef.current = true;
      start();
    } else {
      stop();
    }
    return stop;
  }, [enabled]);

  return { status };
}
