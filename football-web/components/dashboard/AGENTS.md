# Dashboard Components — Agent Notes

## Match Detail Dialog Integration Pattern

Both `match-cards-grid.tsx` and `tournament-bracket.tsx` open the `MatchDetailDialog` on card click:

- **State pattern**: `const [detailMatchId, setDetailMatchId] = useState<number | null>(null)` + `const [detailOpen, setDetailOpen] = useState(false)`
- **Click handler**: `onMatchClick={(id) => { setDetailMatchId(id); setDetailOpen(true) }}`
- **Dialog placement**: `<MatchDetailDialog matchId={detailMatchId} open={detailOpen} onOpenChange={setDetailOpen} />` rendered as sibling in the same container
- **Bracket note**: `BracketMatch.id` is a string, so `parseInt(match.id, 10)` is needed before passing to dialog

## File Split Pattern

`match-detail-dialog.tsx` was split at 600-line limit into:
- `match-detail-dialog.tsx` — Main dialog component + state management + AI analysis section (~555 lines)
- `match-detail-helpers.tsx` — Exported sub-components (EventsSection, StatRow, VenueInfoItem) + types (MatchDetailData, MatchDetailEvent) (~215 lines)

## AI Analysis in MatchDetailDialog

The dialog includes an "AI Analysis" section at the bottom with:
- **Skill selector**: shadcn `Select` component, fetches skills via `getAvailableSkills(lang)` on mount
- **Auto-detect**: Default option uses `recommendedSkillId(stage)` (group→group_stage_predict, else→knockout_stage_predict)
- **Callback**: `onAnalyzeMatch?: (matchData: MatchDetailData, skillId: string) => void` prop — parent component handles the actual SSE streaming
- **Streaming state**: Reads `isStreaming` from `useAIChatStore` to disable button during active analysis
- **i18n keys**: All under `matchDetail.*` namespace (aiAnalysis, selectSkill, autoDetect, etc.)

## Mobile AI Copilot Pattern

`ai-copilot-mobile.tsx` wraps `AICopilotPanel` for mobile:
- **Visibility**: FAB uses `lg:hidden`, desktop sidebar uses `hidden lg:block` — they are mutually exclusive
- **Sheet**: Uses shadcn/ui `Sheet` with `side="bottom"` at `h-[88vh]` for maximum chat space
- **State sharing**: Both mobile and desktop render the same `AICopilotPanel` which reads/writes to the shared `useAIChatStore` Zustand store
- **Streaming indicator**: FAB shows `animate-pulse` + yellow ping dot while `isStreaming` is true
- **Accessibility**: Sheet has `sr-only` header with `SheetTitle` + `SheetDescription` for Radix a11y
