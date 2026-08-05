# dynamic-island

Tauri 2 + React 19 + TypeScript + Vite desktop UI (pnpm). A self-contained demo rendering a
macOS-style "dynamic island"; **not yet connected to the backend**.

## Commands

| Command | Description |
|---------|-------------|
| `pnpm dev` | Vite dev server on port 1420 (strict). |
| `pnpm tauri dev` | Full Tauri dev (runs `pnpm dev` as `beforeDevCommand`). |
| `pnpm build` | `tsc && vite build`. |
| `pnpm tauri build` | Production bundle. |
| `pnpm lint` / `pnpm lint:fix` | Lint with `oxlint`. |
| `pnpm format` / `pnpm format:check` | Format with `oxfmt`. |

Do **not** use `eslint`/`prettier` — this repo's tools are `oxlint` and `oxfmt`.

## Structure

- `src/App.tsx` — renders the DynamicIsland (demo presets, not wired to backend).
- `src/components/DynamicIsland/` — island component, state hook, types.
- `src/components/Alfred/` — voice recorder, wake word, waveform, transcript (directional).
- `src/components/ui/` — shadcn-style components (cva + clsx + tailwind-merge; `cn()` in `lib/utils.ts`).
- `src-tauri/src/lib.rs` — placeholder Rust side (only a `greet` command; `microphone` permission).
- `src/App.bak.tsx` and `src/components/Sample/` are legacy and ignored.

## Stack

- Tailwind v4 via `@tailwindcss/vite`; Vite alias `@/` → `src/`.
- `zustand` for state; `motion` for animations; `@base-ui/react` for primitives.