import { create } from 'zustand';
import { useEffect } from 'react';

export interface RecorderState {
  isRecording: boolean;
  isMuted: boolean;
  transcript: string;
  interimTranscript: string;
  volume: number; // 0-1 for visualiser
  elapsedSeconds: number;
}

interface VoiceRecorderStore extends RecorderState {
  start: () => Promise<void>;
  stop: () => void;
  toggleMute: () => void;
  reset?: () => void; // optional

  // Internal actions (still exposed for get() usage)
  tickVolume: () => void;
  startRecognition: () => void;
}

// Persistent refs outside the store
let recognitionRef: SpeechRecognition | null = null;
let audioContextRef: AudioContext | null = null;
let analyserRef: AnalyserNode | null = null;
let streamRef: MediaStream | null = null;
let sourceRef: MediaStreamAudioSourceNode | null = null;
let animFrameRef = 0;
let timerRef: ReturnType<typeof setInterval> | null = null;
let transcriptRef = "";
let isMutedRef = false;

export const useVoiceRecorderStore = create<VoiceRecorderStore>((set, get) => ({
  // State
  isRecording: false,
  isMuted: false,
  transcript: "",
  interimTranscript: "",
  volume: 0,
  elapsedSeconds: 0,

  // Internal: Volume visualizer
  tickVolume: () => {
    if (!analyserRef) return;

    const data = new Uint8Array(analyserRef.frequencyBinCount);
    analyserRef.getByteFrequencyData(data);
    const avg = data.reduce((sum, value) => sum + value, 0) / data.length / 255;

    set({ volume: isMutedRef ? 0 : Math.min(1, avg) });
    animFrameRef = requestAnimationFrame(get().tickVolume);
  },

  // Internal: Speech Recognition
  startRecognition: () => {
    const SpeechRecognitionAPI = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) return;

    const rec = new SpeechRecognitionAPI();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    recognitionRef = rec;

    rec.onresult = (event: SpeechRecognitionEvent) => {
      if (isMutedRef) return;

      let interim = "";
      let final = transcriptRef;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPart = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += (final ? " " : "") + transcriptPart.trim();
        } else {
          interim = transcriptPart;
        }
      }

      transcriptRef = final;
      set({ transcript: final, interimTranscript: interim });
    };

    rec.onend = () => {
      if (get().isRecording && !isMutedRef) {
        try {
          recognitionRef?.start();
        } catch (e) {}
      }
    };

    try {
      rec.start();
    } catch (e) {}
  },

  // Public Actions
  start: async () => {
    transcriptRef = "";
    isMutedRef = false;

    set({
      isRecording: true,
      isMuted: false,
      transcript: "",
      interimTranscript: "",
      volume: 0,
      elapsedSeconds: 0,
    });

    // Audio stream for volume meter
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef = stream;

      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef = ctx;

      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyserRef = analyser;

      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);
      sourceRef = source;

      animFrameRef = requestAnimationFrame(get().tickVolume);
    } catch (err) {
      console.error("Microphone access denied or failed:", err);
    }

    // Timer
    if (timerRef) clearInterval(timerRef);
    timerRef = setInterval(() => {
      set((state) => ({ elapsedSeconds: state.elapsedSeconds + 1 }));
    }, 1000);

    get().startRecognition();
  },

  stop: () => {
    recognitionRef?.stop();
    cancelAnimationFrame(animFrameRef);
    if (timerRef) clearInterval(timerRef);
    streamRef?.getTracks().forEach((track) => track.stop());
    audioContextRef?.close?.();

    set({
      isRecording: false,
      isMuted: false,
      volume: 0,
    });

    isMutedRef = false;
    transcriptRef = "";
  },

  toggleMute: () => {
    isMutedRef = !isMutedRef;

    streamRef?.getAudioTracks().forEach((track) => {
      track.enabled = !isMutedRef;
    });

    if (isMutedRef) {
      recognitionRef?.stop();
    } else {
      get().startRecognition();
    }

    set((state) => ({ isMuted: !state.isMuted, volume: 0 }));
  },

  reset: () => {
    get().stop();
    transcriptRef = "";
    set({
      transcript: "",
      interimTranscript: "",
      elapsedSeconds: 0,
    });
  },
}));

// Cleanup hook (recommended)
export const useVoiceRecorderCleanup = () => {
  useEffect(() => {
    return () => {
      useVoiceRecorderStore.getState().stop();
    };
  }, []);
};