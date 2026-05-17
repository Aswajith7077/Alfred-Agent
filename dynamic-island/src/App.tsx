// import DynamicIsland from "@/components/Sample/dynamic-island";

// const App = () => {
//   return (
//     <div className="border-2 mx-2 border-black">
//       <DynamicIsland />
//     </div>
//   );
// };

// export default App;

import { useState } from "react";
import { DynamicIsland } from "@/components/DynamicIsland/DynamicIsland";
import { useDynamicIsland } from "@/components/DynamicIsland/useDynamicIsland";
import type { IslandState } from "@/components/DynamicIsland/types";
// import { Button } from "@/components/ui/button";
import "./App.css";

// ── Example right-side widgets ──────────────────────────────────────────────

// function AudioWave() {
//   return (
//     <div className="flex items-end gap-[2px] h-4">
//       {[3, 6, 4, 7, 5, 3, 6].map((h, i) => (
//         <div
//           key={i}
//           className="w-[2px] rounded-full bg-green-400 animate-pulse"
//           style={{
//             height: `${h * 2}px`,
//             animationDelay: `${i * 80}ms`,
//           }}
//         />
//       ))}
//     </div>
//   );
// }

// function TimerDisplay({ seconds }: { seconds: number }) {
//   const m = Math.floor(seconds / 60).toString().padStart(2, "0");
//   const s = (seconds % 60).toString().padStart(2, "0");
//   return (
//     <span className="font-mono text-orange-400 text-xs font-bold">
//       {m}:{s}
//     </span>
//   );
// }

// ── Demo presets ─────────────────────────────────────────────────────────────

const DEMOS = [
  {
    label: "Idle",
    state: "idle" as IslandState,
    content: {},
  },
  {
    label: "Notification",
    state: "compact" as IslandState,
    content: {
      icon: "🔔",
      title: "New message from Alex",
      right: <span className="text-white/40 text-[10px]">now</span>,
    },
  },
  //   {
  //     label: "Music",
  //     state: "expanded" as IslandState,
  //     content: {
  //       icon: "🎵",
  //       title: "Lofi Hip Hop Radio",
  //       subtitle: "Chillhop Music • 128 kbps",
  //       right: <AudioWave />,
  //     },
  //   },
  //   {
  //     label: "Timer",
  //     state: "expanded" as IslandState,
  //     content: {
  //       icon: "⏱️",
  //       title: "Kitchen Timer",
  //       subtitle: "Pasta is almost ready",
  //       right: <TimerDisplay seconds={247} />,
  //     },
  //   },
  {
    label: "Ultra",
    state: "ultra" as IslandState,
    content: {
      icon: "📍",
      title: "Navigation",
      subtitle: "Coimbatore • ETA 12 min",
      right: <span className="text-white/40 text-[10px]">Live</span>,
      expandedContent: (
        <div className="space-y-1.5">
          <div className="flex justify-between">
            <span className="text-white/60">Next turn</span>
            <span className="text-white font-medium">Turn right on NH-544</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60">Distance</span>
            <span className="text-white font-medium">3.2 km</span>
          </div>
          <div className="flex justify-between">
            <span className="text-white/60">Arrival</span>
            <span className="text-green-400 font-medium">4:38 PM</span>
          </div>
        </div>
      ),
    },
  },
];

// ── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const { state, content, show, setState } = useDynamicIsland();
  const [active, setActive] = useState<string>("Idle");

  function activate(demo: (typeof DEMOS)[number]) {
    setActive(demo.label);
    if (demo.state === "idle") {
      setState("idle");
    } else {
      show(demo.content, demo.state);
    }
  }

  return (
    // Simulate Tauri window — remove these wrapper styles in real app
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center pt-6 px-4 font-sans">
      {/* Island sits at the very top, like macOS menu bar */}
      <div className="w-full max-w-md mb-12">
        <DynamicIsland state={state} content={content} onStateChange={(s) => setState(s)} />
      </div>
    </div>
  );
}
