import { useCallback, useEffect, useRef, useState } from "react";

export interface RecorderState {
  isRecording: boolean;
  isMuted: boolean;
  transcript: string;
  interimTranscript: string;
  volume: number; // 0-1 for visualiser
  elapsedSeconds: number;
  isSilence: boolean;
  silenceCountdown: number; // seconds remaining before auto-stop
}

interface UseVoiceRecorderOptions {
  onTranscriptUpdate?: (full: string) => void;
  /** How long volume must stay below `silenceThreshold` before auto-stopping. */
  silenceTimeoutMs?: number;
  /** Volume (0-1) below which audio is considered silent. */
  silenceThreshold?: number;
  onSilenceStop?: () => void;
}

export function useVoiceRecorder({
  onTranscriptUpdate,
  silenceTimeoutMs = 2500,
  silenceThreshold = 0.04,
  onSilenceStop,
}: UseVoiceRecorderOptions = {}) {
  const [state, setState] = useState<RecorderState>({
    isRecording: false,
    isMuted: false,
    transcript: "",
    interimTranscript: "",
    volume: 0,
    elapsedSeconds: 0,
    isSilence: false,
    silenceCountdown: silenceTimeoutMs / 1000,
  });

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const transcriptRef = useRef("");
  const isMutedRef = useRef(false);
  const silenceStartRef = useRef<number | null>(null);
  const silenceTimeoutMsRef = useRef(silenceTimeoutMs);
  const silenceThresholdRef = useRef(silenceThreshold);
  const onSilenceStopRef = useRef(onSilenceStop);
  const stopRef = useRef<() => void>(() => {});

  silenceTimeoutMsRef.current = silenceTimeoutMs;
  silenceThresholdRef.current = silenceThreshold;
  onSilenceStopRef.current = onSilenceStop;

  const tickVolume = useCallback(() => {
    if (!analyserRef.current) return;
    const data = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(data);
    const avg = data.reduce((s, v) => s + v, 0) / data.length / 255;
    const volume = isMutedRef.current ? 0 : avg;

    if (!isMutedRef.current && volume < silenceThresholdRef.current) {
      if (silenceStartRef.current === null) silenceStartRef.current = performance.now();
      const remainingMs = Math.max(
        0,
        silenceTimeoutMsRef.current - (performance.now() - silenceStartRef.current),
      );

      if (remainingMs <= 0) {
        setState((p) => ({ ...p, volume, isSilence: true, silenceCountdown: 0 }));
        stopRef.current();
        onSilenceStopRef.current?.();
        return;
      }

      setState((p) => ({ ...p, volume, isSilence: true, silenceCountdown: remainingMs / 1000 }));
    } else {
      silenceStartRef.current = null;
      setState((p) => ({
        ...p,
        volume,
        isSilence: false,
        silenceCountdown: silenceTimeoutMsRef.current / 1000,
      }));
    }

    animFrameRef.current = requestAnimationFrame(tickVolume);
  }, []);

  const startRecognition = useCallback(() => {
    const SR = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;

    const rec = new SR();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";
    recognitionRef.current = rec;

    rec.onresult = (event: SpeechRecognitionEvent) => {
      if (isMutedRef.current) return;
      let interim = "";
      let final = transcriptRef.current;
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += (final ? " " : "") + t.trim();
        } else {
          interim = t;
        }
      }
      transcriptRef.current = final;
      setState((p) => ({ ...p, transcript: final, interimTranscript: interim }));
      onTranscriptUpdate?.(final);
    };

    rec.onend = () => {
      setState((p) => {
        if (p.isRecording && !isMutedRef.current) {
          try { recognitionRef.current?.start(); } catch {}
        }
        return p;
      });
    };

    try { rec.start(); } catch {}
  }, [onTranscriptUpdate]);

  const start = useCallback(async () => {
    transcriptRef.current = "";
    isMutedRef.current = false;
    silenceStartRef.current = null;
    setState({
      isRecording: true,
      isMuted: false,
      transcript: "",
      interimTranscript: "",
      volume: 0,
      elapsedSeconds: 0,
      isSilence: false,
      silenceCountdown: silenceTimeoutMsRef.current / 1000,
    });

    // Mic stream for volume meter
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const ctx = new AudioContext();
      audioContextRef.current = ctx;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyserRef.current = analyser;
      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);
      sourceRef.current = source;
      animFrameRef.current = requestAnimationFrame(tickVolume);
    } catch {}

    // Timer
    timerRef.current = setInterval(() => {
      setState((p) => ({ ...p, elapsedSeconds: p.elapsedSeconds + 1 }));
    }, 1000);

    startRecognition();
  }, [startRecognition, tickVolume]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    cancelAnimationFrame(animFrameRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close();
    silenceStartRef.current = null;
    setState((p) => ({
      ...p,
      isRecording: false,
      volume: 0,
      isMuted: false,
      isSilence: false,
      silenceCountdown: silenceTimeoutMsRef.current / 1000,
    }));
    isMutedRef.current = false;
  }, []);

  stopRef.current = stop;

  const toggleMute = useCallback(() => {
    isMutedRef.current = !isMutedRef.current;
    silenceStartRef.current = null;
    streamRef.current?.getAudioTracks().forEach((t) => {
      t.enabled = !isMutedRef.current;
    });
    if (isMutedRef.current) {
      recognitionRef.current?.stop();
    } else {
      startRecognition();
    }
    setState((p) => ({
      ...p,
      isMuted: !p.isMuted,
      volume: 0,
      isSilence: false,
      silenceCountdown: silenceTimeoutMsRef.current / 1000,
    }));
  }, [startRecognition]);

  useEffect(() => () => stop(), []);

  return { state, start, stop, toggleMute };
}