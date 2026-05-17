import { motion, AnimatePresence } from "motion/react";
import { AlfredLogo } from "./AlfredLogo";

interface TranscriptModalProps {
  open: boolean;
  transcript: string;
  interimTranscript: string;
  onClose: () => void;
}

export function TranscriptModal({
  open,
  transcript,
  interimTranscript,
  onClose,
}: TranscriptModalProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40"
          />

          {/* Modal */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.94, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 20 }}
            transition={{ type: "spring", stiffness: 400, damping: 32 }}
            className="fixed inset-6 z-50 flex flex-col rounded-3xl bg-zinc-900 border border-white/10 overflow-hidden shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10 flex-shrink-0">
              <div className="w-8 h-8 rounded-xl bg-black flex items-center justify-center">
                <AlfredLogo size={20} />
              </div>
              <div>
                <p className="text-white text-sm font-semibold">Alfred Transcript</p>
                <p className="text-white/40 text-xs">Full session log</p>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <button
                  onClick={() => navigator.clipboard.writeText(transcript)}
                  className="text-white/40 hover:text-white/80 transition-colors p-2 rounded-lg hover:bg-white/5 text-xs"
                >
                  Copy
                </button>
                <button
                  onClick={onClose}
                  className="text-white/40 hover:text-white/80 transition-colors p-2 rounded-lg hover:bg-white/5"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Transcript body */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-1">
              {transcript ? (
                <>
                  <p className="text-white/90 text-sm leading-relaxed whitespace-pre-wrap">
                    {transcript}
                  </p>
                  {interimTranscript && (
                    <p className="text-white/40 text-sm italic leading-relaxed">
                      {interimTranscript}
                    </p>
                  )}
                </>
              ) : (
                <p className="text-white/30 text-sm italic">
                  Listening… start speaking to see the transcript here.
                </p>
              )}
            </div>

            {/* Word count footer */}
            <div className="px-6 py-3 border-t border-white/10 flex items-center justify-between flex-shrink-0">
              <span className="text-white/30 text-xs">
                {transcript.split(/\s+/).filter(Boolean).length} words
              </span>
              <span className="text-white/30 text-xs">{transcript.length} characters</span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
