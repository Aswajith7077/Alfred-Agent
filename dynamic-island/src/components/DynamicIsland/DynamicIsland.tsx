import { motion, AnimatePresence } from "motion/react";
import type { DynamicIslandProps, IslandState } from "./types";
import { cn } from "@/lib/utils";

// Size map per state
const sizeMap: Record<IslandState, { width: number | string; height: number }> = {
  idle: { width: 120, height: 34 },
  compact: { width: 260, height: 34 },
  expanded: { width: 360, height: 80 },
  ultra: { width: 720, height: 200 },
};

const springConfig = {
  type: "spring" as const,
  stiffness: 500,
  damping: 38,
  mass: 0.8,
};

export function DynamicIsland({ state = "idle", content = {}, onStateChange }: DynamicIslandProps) {
  const { width, height } = sizeMap[state];

  return (
    <div className="flex items-start justify-center w-full pointer-events-none select-none">
      <motion.div
        layout
        animate={{ width, height }}
        transition={springConfig}
        onClick={() => {
          if (state === "compact") onStateChange?.("expanded");
          else if (state === "expanded") onStateChange?.("compact");
        }}
        className={cn(
          "relative overflow-hidden rounded-[22px] bg-black shadow-2xl cursor-pointer pointer-events-auto",
          "ring-1 ring-white/10",
          state !== "idle" && "shadow-black/60",
        )}
        style={{ willChange: "width, height, border-radius" }}
      >
        {/* Gloss overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent pointer-events-none z-10 rounded-xl" />

        {/* Idle pill — just the camera dot */}
        <AnimatePresence mode="wait">
          {state === "idle" && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              className="absolute inset-0 flex items-center justify-center"
            >
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-800 ring-1 ring-white/5" />
            </motion.div>
          )}

          {/* Compact — single-line with icon + text */}
          {state === "compact" && (
            <motion.div
              key="compact"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0 flex items-center justify-between px-3 gap-2"
            >
              {/* Left: icon + title */}
              <div className="flex items-center gap-2 min-w-0">
                {content.icon && (
                  <span className="text-white flex-shrink-0 text-base">{content.icon}</span>
                )}
                <span className="text-white text-xs font-medium truncate">{content.title}</span>
              </div>

              {/* Right side slot */}
              {content.right && (
                <div className="flex-shrink-0 text-white/70 text-base">{content.right}</div>
              )}
            </motion.div>
          )}

          {/* Expanded — two-line with subtitle */}
          {state === "expanded" && (
            <motion.div
              key="expanded"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              transition={{ duration: 0.22 }}
              className="absolute inset-0 flex items-center px-4 gap-3"
            >
              {content.icon && (
                <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center text-white text-lg">
                  {content.icon}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-semibold truncate leading-tight">
                  {content.title}
                </p>
                {content.subtitle && (
                  <p className="text-white/50 text-xs truncate mt-0.5">{content.subtitle}</p>
                )}
              </div>
              {content.right && <div className="flex-shrink-0">{content.right}</div>}
            </motion.div>
          )}

          {/* Ultra — full expanded content */}
          {state === "ultra" && (
            <motion.div
              key="ultra"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.25 }}
              className="absolute inset-0 flex flex-col px-4 py-3 gap-2"
            >
              {/* Header */}
              <div className="flex items-center gap-2">
                {content.icon && (
                  <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center text-white text-sm">
                    {content.icon}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-white text-xs font-semibold truncate">{content.title}</p>
                  {content.subtitle && (
                    <p className="text-white/40 text-[10px] truncate">{content.subtitle}</p>
                  )}
                </div>
                {content.right && <div className="flex-shrink-0">{content.right}</div>}
              </div>

              {/* Divider */}
              <div className="h-px bg-white/10" />

              {/* Body */}
              <div className="flex-1 overflow-hidden text-white/80 text-xs">
                {content.expandedContent}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
