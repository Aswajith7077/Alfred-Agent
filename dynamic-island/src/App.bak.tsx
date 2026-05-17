// // import { useState } from "react";
// // import { DynamicIsland } from "@/components/DynamicIsland/DynamicIsland";
// // import { useDynamicIsland } from "@/components/DynamicIsland/useDynamicIsland";
// // import type { IslandState } from "@/components/DynamicIsland/types";
// // import { Button } from "@/components/ui/button";
// // import './App.css'

// // // ── Example right-side widgets ──────────────────────────────────────────────

// // function AudioWave() {
// //   return (
// //     <div className="flex items-end gap-[2px] h-4">
// //       {[3, 6, 4, 7, 5, 3, 6].map((h, i) => (
// //         <div
// //           key={i}
// //           className="w-[2px] rounded-full bg-green-400 animate-pulse"
// //           style={{
// //             height: `${h * 2}px`,
// //             animationDelay: `${i * 80}ms`,
// //           }}
// //         />
// //       ))}
// //     </div>
// //   );
// // }

// // function TimerDisplay({ seconds }: { seconds: number }) {
// //   const m = Math.floor(seconds / 60).toString().padStart(2, "0");
// //   const s = (seconds % 60).toString().padStart(2, "0");
// //   return (
// //     <span className="font-mono text-orange-400 text-xs font-bold">
// //       {m}:{s}
// //     </span>
// //   );
// // }

// // // ── Demo presets ─────────────────────────────────────────────────────────────

// // const DEMOS = [
// //   {
// //     label: "Idle",
// //     state: "idle" as IslandState,
// //     content: {},
// //   },
// //   {
// //     label: "Notification",
// //     state: "compact" as IslandState,
// //     content: {
// //       icon: "🔔",
// //       title: "New message from Alex",
// //       right: <span className="text-white/40 text-[10px]">now</span>,
// //     },
// //   },
// //   {
// //     label: "Music",
// //     state: "expanded" as IslandState,
// //     content: {
// //       icon: "🎵",
// //       title: "Lofi Hip Hop Radio",
// //       subtitle: "Chillhop Music • 128 kbps",
// //       right: <AudioWave />,
// //     },
// //   },
// //   {
// //     label: "Timer",
// //     state: "expanded" as IslandState,
// //     content: {
// //       icon: "⏱️",
// //       title: "Kitchen Timer",
// //       subtitle: "Pasta is almost ready",
// //       right: <TimerDisplay seconds={247} />,
// //     },
// //   },
// //   {
// //     label: "Ultra",
// //     state: "ultra" as IslandState,
// //     content: {
// //       icon: "📍",
// //       title: "Navigation",
// //       subtitle: "Coimbatore • ETA 12 min",
// //       right: <span className="text-white/40 text-[10px]">Live</span>,
// //       expandedContent: (
// //         <div className="space-y-1.5">
// //           <div className="flex justify-between">
// //             <span className="text-white/60">Next turn</span>
// //             <span className="text-white font-medium">Turn right on NH-544</span>
// //           </div>
// //           <div className="flex justify-between">
// //             <span className="text-white/60">Distance</span>
// //             <span className="text-white font-medium">3.2 km</span>
// //           </div>
// //           <div className="flex justify-between">
// //             <span className="text-white/60">Arrival</span>
// //             <span className="text-green-400 font-medium">4:38 PM</span>
// //           </div>
// //         </div>
// //       ),
// //     },
// //   },
// // ];

// // // ── Main App ─────────────────────────────────────────────────────────────────

// // export default function App() {
// //   const { state, content, show, setState } = useDynamicIsland();
// //   const [active, setActive] = useState<string>("Idle");

// //   function activate(demo: (typeof DEMOS)[number]) {
// //     setActive(demo.label);
// //     if (demo.state === "idle") {
// //       setState("idle");
// //     } else {
// //       show(demo.content, demo.state);
// //     }
// //   }

// //   return (
// //     // Simulate Tauri window — remove these wrapper styles in real app
// //     <div className="min-h-screen bg-zinc-950 flex flex-col items-center pt-6 px-4 font-sans">
// //       {/* Island sits at the very top, like macOS menu bar */}
// //       <div className="w-full max-w-md mb-12">
// //         <DynamicIsland
// //           state={state}
// //           content={content}
// //           onStateChange={(s) => setState(s)}
// //         />
// //       </div>

// //       {/* Demo controls */}
// //       <div className="w-full max-w-md space-y-6">
// //         <p className="text-zinc-500 text-xs uppercase tracking-widest text-center">
// //           Demo states
// //         </p>
// //         <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
// //           {DEMOS.map((d) => (
// //             <Button
// //               key={d.label}
// //               variant={active === d.label ? "default" : "outline"}
// //               size="sm"
// //               onClick={() => activate(d)}
// //               className={
// //                 active === d.label
// //                   ? "bg-white text-black hover:bg-white/90"
// //                   : "border-zinc-700 text-zinc-300 hover:bg-zinc-800"
// //               }
// //             >
// //               {d.label}
// //             </Button>
// //           ))}
// //         </div>

// //         <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4 text-xs text-zinc-400 space-y-1.5">
// //           <p className="text-zinc-200 font-medium text-sm">Usage in your code</p>
// //           <pre className="overflow-auto text-[11px] leading-relaxed text-zinc-500">
// // {`const { state, content, show, dismiss } = useDynamicIsland();

// // // Show a compact notification for 3 s
// // show({ icon: "🔔", title: "Done!" }, "compact", 3000);

// // // Show expanded music player
// // show({
// //   icon: "🎵", title: "Song Title",
// //   subtitle: "Artist", right: <AudioWave />
// // }, "expanded");

// // // Dismiss manually
// // dismiss();`}
// //           </pre>
// //         </div>
// //       </div>
// //     </div>
// //   );
// // }

// import { AlfredIsland } from "@/components/Alfred/AlfredIsland";
// import './App.css'

// export default function App() {
//   return (
//     // Tauri window root — add data-tauri-drag-region to the bar div in your layout
//     <div className="min-h-screen bg-zinc-950 flex flex-col items-center px-4">

//       {/* ── Island bar — mimics top OS bar ── */}
//       {/* In Tauri: add data-tauri-drag-region here so the bar is draggable */}
//       <div
//         data-tauri-drag-region
//         className="w-full flex justify-center pt-3 pb-2"
//       >
//         <AlfredIsland />
//       </div>

//       {/* ── Demo hint card ── */}
//       <div className="mt-16 max-w-sm w-full rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 text-center space-y-3">
//         <div className="w-12 h-12 rounded-2xl bg-black border border-zinc-800 flex items-center justify-center mx-auto">
//           {/* bat logo inline */}
//           <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
//             <ellipse cx="16" cy="20" rx="5" ry="6" fill="white" opacity="0.9" />
//             <path d="M11 19 C 6 16, 2 20, 3 24 C 5 22, 8 21, 11 22 Z" fill="white" opacity="0.85" />
//             <path d="M21 19 C 26 16, 30 20, 29 24 C 27 22, 24 21, 21 22 Z" fill="white" opacity="0.85" />
//             <path d="M13 15 L11 9 L15 14 Z" fill="white" opacity="0.9" />
//             <path d="M19 15 L21 9 L17 14 Z" fill="white" opacity="0.9" />
//             <circle cx="14" cy="19" r="1" fill="black" />
//             <circle cx="18" cy="19" r="1" fill="black" />
//           </svg>
//         </div>

//         <div>
//           <p className="text-white font-semibold text-sm">Alfred is listening</p>
//           <p className="text-zinc-500 text-xs mt-1 leading-relaxed">
//             Say <span className="text-white/70 font-mono bg-white/5 px-1.5 py-0.5 rounded">"Hey Alfred"</span> or{" "}
//             <span className="text-white/70 font-mono bg-white/5 px-1.5 py-0.5 rounded">"Batman speaking"</span>{" "}
//             to wake the island
//           </p>
//         </div>

//         <div className="grid grid-cols-2 gap-2 text-left pt-1">
//           {[
//             { icon: "🎙️", label: "Compact", desc: "Wakes & listens" },
//             { icon: "〰️", label: "Recording", desc: "Wave + mute + stop" },
//             { icon: "📄", label: "Transcribed", desc: "Scrollable transcript" },
//             { icon: "⛶", label: "Full screen", desc: "Expand modal view" },
//           ].map((s) => (
//             <div key={s.label} className="rounded-xl bg-zinc-800/60 px-3 py-2">
//               <p className="text-white/80 text-xs font-medium">
//                 {s.icon} {s.label}
//               </p>
//               <p className="text-zinc-500 text-[10px] mt-0.5">{s.desc}</p>
//             </div>
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }
