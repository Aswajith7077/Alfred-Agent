import type { DynamicIslandProps, IslandState } from "./types";
import { motion, AnimatePresence } from "motion/react";
import ExpandedContent from "@/components/Sample/DynamicIslandSubComps/expanded-content";
import CompactContent from "@/components/Sample/DynamicIslandSubComps/compact-content";
import { cn } from "@/lib/utils";

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

const DynamicIsland = ({ state = "idle", content = {}, onStateChange }: DynamicIslandProps) => {
  const { width, height } = sizeMap[state];
  return (
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
      <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent pointer-events-none z-10 rounded-xl" />
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
        {state === "compact" && <CompactContent content={content} />}

        {/* Expanded — two-line with subtitle */}
        {state === "expanded" && <ExpandedContent content={content} />}

        {/* Ultra — full expanded content */}
        {/* {state === "ultra" && <UltraContent content={content} />} */}
      </AnimatePresence>
    </motion.div>
  );
};

export default DynamicIsland;
