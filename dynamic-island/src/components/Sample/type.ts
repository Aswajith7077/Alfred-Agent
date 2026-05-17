export type IslandState = "idle" | "compact" | "expanded" | "ultra";

export interface IslandContent {
  icon?: React.ReactNode;
  title?: string;
  subtitle?: string;
  left?: React.ReactNode;
  right?: React.ReactNode;
  expandedContent?: React.ReactNode;
}

export interface DynamicIslandProps {
  state?: IslandState;
  content?: IslandContent;
  onStateChange?: (state: IslandState) => void;
}

export type SubComponentProps = {
  content: IslandContent;
};

export interface RecorderState {
  isRecording: boolean;
  isMuted: boolean;
  transcript: string;
  interimTranscript: string;
  volume: number;
  elapsedSeconds: number;
  silenceCountdown: number; // counts DOWN 2.5 → 0 during grace period
  isSilence: boolean; // true during the grace period
}

export interface UseVoiceRecorderOptions {
  onTranscriptUpdate?: (full: string) => void;
  onSilenceStop?: () => void;
  silenceTimeoutMs?: number;
  silenceThreshold?: number; // 0–1 volume below this = silence
}
