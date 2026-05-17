import { useState, useCallback, useRef } from "react";
import type { IslandState, IslandContent } from "./types";

export function useDynamicIsland(defaultState: IslandState = "idle") {
  const [state, setState] = useState<IslandState>(defaultState);
  const [content, setContent] = useState<IslandContent>({});
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = useCallback(
    (newContent: IslandContent, newState: IslandState = "compact", duration?: number) => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setContent(newContent);
      setState(newState);

      if (duration) {
        timeoutRef.current = setTimeout(() => {
          setState("idle");
          setContent({});
        }, duration);
      }
    },
    [],
  );

  const expand = useCallback((expandedContent?: React.ReactNode) => {
    if (expandedContent) {
      setContent((prev) => ({ ...prev, expandedContent }));
    }
    setState("expanded");
  }, []);

  const collapse = useCallback(() => {
    setState("compact");
  }, []);

  const dismiss = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setState("idle");
    setTimeout(() => setContent({}), 400);
  }, []);

  const setUltra = useCallback((expandedContent?: React.ReactNode) => {
    if (expandedContent) {
      setContent((prev) => ({ ...prev, expandedContent }));
    }
    setState("ultra");
  }, []);

  return { state, content, show, expand, collapse, dismiss, setUltra, setState };
}
