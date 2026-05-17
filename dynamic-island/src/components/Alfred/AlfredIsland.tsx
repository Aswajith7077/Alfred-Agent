import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useWakeWord } from "./useWakeWord";
import { useVoiceRecorder } from "./useVoiceRecorder";
import { VoiceWave } from "@/components/Alfred/VoiceWave";
import { AlfredLogo } from "@/components/Alfred/AlfredLogo";
import { TranscriptModal } from "@/components/Alfred/TranscriptModal";
import { BarVisualizer, type AgentState } from "@/components/ui/bar-visualizer";
import { LiveWaveform } from "@/components/ui/live-waveform";
import { cn } from "@/lib/utils";
import { HugeiconsIcon } from "@hugeicons/react";
import { DashboardSquare03Icon, Mic02Icon } from "@hugeicons/core-free-icons";

// ─── Types ────────────────────────────────────────────────────────────────────

type AlfredMode = "idle" | "waking" | "compact" | "recording" | "transcribed";

// ─── Spring ───────────────────────────────────────────────────────────────────

const spring = { type: "spring" as const, stiffness: 480, damping: 38, mass: 0.8 };

// ─── Size map ─────────────────────────────────────────────────────────────────

const sizes: Record<AlfredMode, { width: number; height: number }> = {
  idle: { width: 150, height: 34 },
  waking: { width: 200, height: 34 },
  compact: { width: 280, height: 36 },
  recording: { width: 380, height: 100 },
  transcribed: { width: 400, height: 170 },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatTime(s: number) {
  const m = Math.floor(s / 60)
    .toString()
    .padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}

// Maps recorder state → BarVisualizer AgentState
function toAgentState(isMuted: boolean, isSilence: boolean, volume: number): AgentState {
  if (isMuted) return "thinking"; // grey pulsing bars
  if (isSilence) return "initializing"; // slow idle
  if (volume > 0.08) return "speaking"; // tall energetic bars
  return "listening"; // soft ambient bars
}

// ─── Silence ring (SVG countdown arc) ────────────────────────────────────────

function SilenceRing({ countdown }: { countdown: number }) {
  const r = 9;
  const circ = 2 * Math.PI * r;
  // countdown goes 2.5 → 0; we want full ring at 2.5, empty at 0
  const progress = countdown / 2.5;
  const dashOffset = circ * (1 - progress);

  return (
    <svg width="24" height="24" viewBox="0 0 24 24" className="flex-shrink-0">
      {/* Track */}
      <circle cx="12" cy="12" r={r} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="2" />
      {/* Progress arc */}
      <circle
        cx="12"
        cy="12"
        r={r}
        fill="none"
        stroke="rgba(251,191,36,0.8)"
        strokeWidth="2"
        strokeDasharray={circ}
        strokeDashoffset={dashOffset}
        strokeLinecap="round"
        transform="rotate(-90 12 12)"
        style={{ transition: "stroke-dashoffset 0.1s linear" }}
      />
      {/* Countdown number */}
      <text
        x="12"
        y="16"
        textAnchor="middle"
        fontSize="7"
        fill="rgba(251,191,36,0.9)"
        fontFamily="monospace"
      >
        {countdown.toFixed(1)}
      </text>
    </svg>
  );
}

// ─── Mic icon ─────────────────────────────────────────────────────────────────

function MicIcon({ muted }: { muted: boolean }) {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
    >
      {muted ? (
        <>
          <line x1="1" y1="1" x2="23" y2="23" />
          <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
          <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </>
      ) : (
        <>
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </>
      )}
    </svg>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function AlfredIsland() {
  const [mode, setMode] = useState<AlfredMode>("idle");
  const [modalOpen, setModalOpen] = useState(false);

  const {
    state: rec,
    start: startRec,
    stop: stopRec,
    toggleMute,
  } = useVoiceRecorder({
    silenceTimeoutMs: 2500,
    silenceThreshold: 0.04,
    onTranscriptUpdate: (t) => {
      if (t.length > 0 && mode === "recording") setMode("transcribed");
    },
    onSilenceStop: () => {
      // Auto-stopped by silence — go to transcribed if we have text, else idle
      setMode((prev) =>
        prev === "recording" || prev === "transcribed"
          ? rec.transcript
            ? "transcribed"
            : "idle"
          : prev,
      );
    },
  });

  // Wake word: requires "Hey Alfred, Batman Speaking" in same utterance
  const handleWakeWord = useCallback(async () => {
    if (mode !== "idle") return;
    setMode("waking");
    await new Promise((r) => setTimeout(r, 600));
    setMode("compact");
    await new Promise((r) => setTimeout(r, 400));
    setMode("recording");
    startRec();
  }, [mode, startRec]);

  const handleStop = useCallback(() => {
    stopRec();
    setMode(rec.transcript ? "transcribed" : "idle");
  }, [stopRec, rec.transcript]);

  const handleDismiss = useCallback(() => {
    stopRec();
    setMode("idle");
  }, [stopRec]);

  useWakeWord({
    phrases: ["hey alfred batman speaking"], // kept for type compat
    onDetected: handleWakeWord,
    enabled: mode === "idle",
  });

  const { width, height } = sizes[mode];
  const agentState = toAgentState(rec.isMuted, rec.isSilence, rec.volume);

  return (
    <>
      <div className="flex justify-center w-full">
        <motion.div
          layout
          animate={{ width, height }}
          transition={spring}
          className={cn(
            "relative overflow-hidden rounded-[22px] bg-black ring-1 ring-white/10 shadow-2xl shadow-black/60",
          )}
          style={{ willChange: "width, height" }}
        >
          {/* Gloss overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/8 to-transparent pointer-events-none z-10 rounded-[22px]" />

          <AnimatePresence mode="wait">
            {/* ── IDLE ── */}
            {mode === "idle" && (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18 }}
                className="absolute inset-0 flex items-center justify-center gap-2"
              >
                <div className="w-2.5 h-2.5 rounded-full bg-zinc-700 ring-1 ring-white/5" />
                <span className="text-white/30 text-[10px] tracking-widest uppercase">alfred</span>
              </motion.div>
            )}

            {/* ── WAKING ── */}
            {mode === "waking" && (
              <motion.div
                key="waking"
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="absolute inset-0 flex items-center justify-center gap-2.5"
              >
                <div className="w-5 h-5 rounded-lg bg-white/10 flex items-center justify-center">
                  <AlfredLogo size={14} />
                </div>
                <span className="text-white/70 text-xs tracking-wide">Waking up…</span>
                <motion.div
                  animate={{ scale: [1, 1.4, 1], opacity: [0.6, 1, 0.6] }}
                  transition={{ repeat: Infinity, duration: 0.8 }}
                  className="w-1.5 h-1.5 rounded-full bg-green-400"
                />
              </motion.div>
            )}

            {/* ── COMPACT ── */}
            {mode === "compact" && (
              <motion.div
                key="compact"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.18 }}
                className="absolute inset-0 flex items-center px-3 gap-2.5"
              >
                <div className="w-6 h-6 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <AlfredLogo size={16} />
                </div>
                <span className="text-white text-xs font-medium flex-1">Listening…</span>
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ repeat: Infinity, duration: 1.2 }}
                  className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0"
                />
              </motion.div>
            )}

            {/* ── RECORDING — BarVisualizer + silence ring ── */}
            {mode === "recording" && (
              <motion.div
                key="recording"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.22 }}
                className="absolute inset-0 flex flex-col px-4 py-3 gap-1.5"
              >
                {/* Header row */}
                <div className="flex items-center gap-2.5">
                  <div className="w-20 h-20 rounded-xl bg-white/10 flex items-center justify-center flex-shrink-0">
                    <AlfredLogo size={18} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-white text-lg font-semibold leading-tight">Alfred</p>
                    <p
                      className="text-[10px] leading-tight"
                      style={{
                        color: rec.isSilence
                          ? "rgba(251,191,36,0.8)"
                          : rec.isMuted
                            ? "rgba(239,68,68,0.7)"
                            : "rgba(255,255,255,0.4)",
                      }}
                    >
                      {rec.isSilence
                        ? `Silence detected — stopping in ${rec.silenceCountdown.toFixed(1)}s`
                        : rec.isMuted
                          ? "Muted"
                          : "Recording…"}
                    </p>
                  </div>

                  {/* Silence countdown ring */}
                  {rec.isSilence && <SilenceRing countdown={rec.silenceCountdown} />}

                  {/* Timer */}
                  <span className="text-white/50 font-mono text-base flex-shrink-0">
                    {formatTime(rec.elapsedSeconds)}
                  </span>

                  {/* Mute toggle */}
                  <button
                    onClick={toggleMute}
                    title={rec.isMuted ? "Unmute" : "Mute"}
                    className={cn(
                      "p-2 rounded-full flex items-center justify-center flex-shrink-0 transition-colors",
                      rec.isMuted
                        ? "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                        : "bg-white/10 text-white/60 hover:bg-white/20",
                    )}
                  >
                    <HugeiconsIcon icon={Mic02Icon} size={20} color="white" strokeWidth={2} />
                  </button>

                  {/* Stop */}
                  <button
                    onClick={handleStop}
                    title="Stop recording"
                    className="p-2.5 rounded-full bg-red-500/80 hover:bg-red-500 flex items-center justify-center flex-shrink-0 transition-colors"
                  >
                    <div className="w-4 h-4 rounded-[2px] bg-white" />
                  </button>
                </div>

                {/* BarVisualizer from ElevenLabs */}
                <div className="flex-1">
                  <BarVisualizer
                    state={agentState}
                    barCount={24}
                    minHeight={10}
                    maxHeight={100}
                    className="h-full w-full"
                    style={
                      {
                        "--bar-color": rec.isMuted
                          ? "rgba(255,255,255,0.2)"
                          : rec.isSilence
                            ? "rgba(251,191,36,0.6)"
                            : "rgba(74,222,128,0.85)",
                      } as React.CSSProperties
                    }
                  />
                </div>
              </motion.div>
            )}

            {/* ── TRANSCRIBED — LiveWaveform + scrollable text ── */}
            {mode === "transcribed" && (
              <motion.div
                key="transcribed"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.25 }}
                className="absolute inset-0 flex flex-col px-4 py-3 gap-2"
              >
                {/* Header */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="w-20 h-20 rounded-xl bg-white/10 flex items-center justify-center flex-shrink-0">
                    <AlfredLogo size={18} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-white text-lg font-semibold">Alfred</p>
                    <p className="text-white/40 text-sm">
                      {rec.isRecording
                        ? rec.isSilence
                          ? `Stopping in ${rec.silenceCountdown.toFixed(1)}s…`
                          : "Still recording…"
                        : "Transcript ready"}
                    </p>
                  </div>

                  {/* Mini LiveWaveform if mic is still active */}
                  {rec.isRecording && (
                    <div className="w-20 h-5 flex-shrink-0">
                      <LiveWaveform
                        active={rec.isRecording && !rec.isMuted}
                        processing={rec.isSilence}
                        height={20}
                        barWidth={2}
                        barGap={1}
                        mode="static"
                        fadeEdges
                        barColor="gray"
                        historySize={40}
                      />
                    </div>
                  )}

                  {/* Mute (only while still recording) */}
                  {rec.isRecording && (
                    <button
                      onClick={toggleMute}
                      title={rec.isMuted ? "Unmute" : "Mute"}
                      className={cn(
                        "w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition-colors",
                        rec.isMuted
                          ? "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                          : "bg-white/10 text-white/60 hover:bg-white/20",
                      )}
                    >
                      <MicIcon muted={rec.isMuted} />
                    </button>
                  )}

                  {/* Expand to full screen */}
                  <button
                    onClick={() => setModalOpen(true)}
                    title="Expand transcript"
                    className="p-2 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center flex-shrink-0 transition-colors text-white/60"
                  >
                    <HugeiconsIcon
                      icon={DashboardSquare03Icon}
                      size={20}
                      color="white"
                      strokeWidth={1.5}
                    />
                  </button>

                  {/* Dismiss */}
                  <button
                    onClick={handleDismiss}
                    title="Dismiss"
                    className="p-2 rounded-full bg-white/5 hover:bg-white/15 flex items-center justify-center flex-shrink-0 transition-colors text-white/40 hover:text-white/80"
                  >
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    >
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>

                {/* Divider */}
                <div className="h-px bg-white/8 flex-shrink-0" />

                {/* Scrollable transcript */}
                <div className="flex-1 overflow-y-hidden" style={{ scrollbarWidth: "none" }}>
                  <p className="text-white/80 text-base leading-relaxed">
                    {rec.transcript}
                    {rec.interimTranscript && (
                      <span className="text-white/30 italic"> {rec.interimTranscript}</span>
                    )}
                  </p>
                  {!rec.transcript && (
                    <p className="text-white/25 text-[11px] italic">Transcript will appear here…</p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      <TranscriptModal
        open={modalOpen}
        transcript={rec.transcript}
        interimTranscript={rec.interimTranscript}
        onClose={() => setModalOpen(false)}
      />
    </>
  );
}
