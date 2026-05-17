import { motion } from "motion/react";

interface VoiceWaveProps {
  volume: number; // 0-1
  isMuted: boolean;
  barCount?: number;
}

export function VoiceWave({ volume, isMuted, barCount = 18 }: VoiceWaveProps) {
  return (
    <div className="flex items-center justify-center gap-[2px] h-full w-full">
      {Array.from({ length: barCount }).map((_, i) => {
        const center = barCount / 2;
        const distFromCenter = Math.abs(i - center) / center;
        // Bell-curve envelope: bars near center are taller
        const envelope = 1 - distFromCenter * 0.7;
        // Randomize phase per bar
        const phase = (i / barCount) * Math.PI * 2;
        const baseHeight = 3;
        const maxHeight = 22;
        const animated = !isMuted && volume > 0.02;
        const targetHeight = animated
          ? baseHeight + (maxHeight - baseHeight) * volume * envelope
          : baseHeight;

        return (
          <motion.div
            key={i}
            animate={{
              height: targetHeight,
              opacity: isMuted ? 0.3 : 0.9,
            }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 20,
              delay: animated ? (phase / (Math.PI * 2)) * 0.05 : 0,
            }}
            className="rounded-full flex-shrink-0"
            style={{
              width: 2,
              background: isMuted
                ? "rgba(255,255,255,0.3)"
                : `rgba(${74 + Math.round(volume * 60)}, 222, ${128 + Math.round(volume * 40)}, 0.85)`,
            }}
          />
        );
      })}
    </div>
  );
}
