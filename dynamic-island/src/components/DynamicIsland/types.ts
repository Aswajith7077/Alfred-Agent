export type IslandState = "idle" | "compact" | "expanded" | "ultra";

export interface IslandContent {
  icon?: React.ReactNode;
  title?: string;
  subtitle?: string;
  left?: React.ReactNode;
  right?: React.ReactNode;
  expandedContent?: React.ReactNode;
}

export interface DynamicIslandProps {
  state?: IslandState;
  content?: IslandContent;
  onStateChange?: (state: IslandState) => void;
}
