import { create } from "zustand";
import { useRef } from "react"; // still needed for the timeout ref
import { IslandState, IslandContent } from "./types";

interface DynamicIslandStore {
  state: IslandState;
  content: IslandContent;

  show: (newContent: IslandContent, newState?: IslandState, duration?: number) => void;
  expand: (expandedContent?: React.ReactNode) => void;
  collapse: () => void;
  dismiss: () => void;
  setUltra: (expandedContent?: React.ReactNode) => void;
  setState: (newState: IslandState) => void;
  reset: () => void; // optional helper
}

export const useDynamicIslandStore = create<DynamicIslandStore>((set, get) => {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  return {
    state: "idle",
    content: {},

    show: (newContent, newState = "compact", duration) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }

      set({
        content: newContent,
        state: newState,
      });

      if (duration) {
        timeoutRef.current = setTimeout(() => {
          set({ state: "idle", content: {} });
        }, duration);
      }
    },

    expand: (expandedContent) => {
      if (expandedContent) {
        set((prev) => ({
          content: { ...prev.content, expandedContent },
        }));
      }
      set({ state: "expanded" });
    },

    collapse: () => {
      set({ state: "compact" });
    },

    dismiss: () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }

      set({ state: "idle" });

      // Match original behavior with delay before clearing content
      setTimeout(() => {
        set({ content: {} });
      }, 400);
    },

    setUltra: (expandedContent) => {
      if (expandedContent) {
        set((prev) => ({
          content: { ...prev.content, expandedContent },
        }));
      }
      set({ state: "ultra" });
    },

    setState: (newState) => set({ state: newState }),

    reset: () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      set({ state: "idle", content: {} });
    },
  };
});
