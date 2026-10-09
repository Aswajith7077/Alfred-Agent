// import DynamicIsland from "@/components/Sample/dynamic-island";

// const App = () => {
//   return (
//     <div className="border-2 mx-2 border-black">
//       <DynamicIsland />
//     </div>
//   );
// };

// export default App;

import { DynamicIsland } from "@/components/DynamicIsland/DynamicIsland";
import { useDynamicIsland } from "@/components/DynamicIsland/useDynamicIsland";
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

// ── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const { state, content, setState } = useDynamicIsland();

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
