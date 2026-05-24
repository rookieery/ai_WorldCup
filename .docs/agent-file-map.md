# Agent File Map

> Navigate the codebase by purpose.

## Root

```
ai_WorldCup/
├── CLAUDE.md                 # Engineering standards (highest priority)
├── prompt.md                 # Ralph agent loop instructions
├── prd.json                  # Story tracker (branch + stories with passes flag)
├── progress.txt              # Ralph execution progress log
├── archive.js                # Unknown utility (standalone script)
├── ralph.sh                  # Shell entry point for Ralph agent
├── .claudeignore             # Claude ignore rules
├── .docs/                    # This documentation directory
├── data/                     # Raw tournament data
├── skills/                   # AI prediction skill definitions
├── football-web/             # Next.js frontend (MAIN APP)
└── football-server/          # Backend (EMPTY — not yet started)
```

## football-web/ — Frontend (Next.js 16 + React 19)

```
football-web/
├── app/
│   ├── layout.tsx            # Root layout (dark theme, Geist fonts, Analytics)
│   ├── page.tsx              # Single-page dashboard (all state lives here)
│   └── globals.css           # CSS variables, animations, glassmorphism utilities
├── components/
│   ├── dashboard/
│   │   ├── header.tsx        # Top bar (timezone + view mode toggles)
│   │   ├── date-timeline.tsx # Horizontal date picker (Jun 11–Jul 19)
│   │   ├── match-cards-grid.tsx  # Match card list + Fan Cheer Meter
│   │   ├── tournament-bracket.tsx # Knockout bracket (QF→SF→F, SVG connectors)
│   │   └── ai-copilot-panel.tsx   # AI chat sidebar (messages, radar chart, analysis)
│   ├── theme-provider.tsx    # next-themes wrapper (unused in layout currently)
│   └── ui/                   # shadcn/ui primitives (~60 components)
├── hooks/
│   ├── use-mobile.ts         # Mobile breakpoint hook
│   └── use-toast.ts          # Toast hook
├── lib/
│   └── utils.ts              # cn() utility (clsx + tailwind-merge)
├── styles/
│   └── globals.css           # Duplicate/alternate globals (check relevance)
├── package.json              # Dependencies (next 16, recharts, date-fns, zod, etc.)
├── components.json           # shadcn/ui config (new-york style, RSC enabled)
├── tsconfig.json             # TypeScript config
├── next.config.mjs           # Next.js config
└── postcss.config.mjs        # PostCSS config
```

## data/ — Tournament Data

```
data/
├── 2026_FIFA_World_Cup_Group_Stage.md  # 12 groups × 6 matches (72 total), results TBD
└── 2022_FIFA_World_Cup_Results.md      # Qatar 2022 results (64 matches, Chinese)
```

## skills/ — AI Prediction Prompts

```
skills/
├── README.md                     # Skills overview
├── group_stage_predict.md        # 6-step reasoning for group match prediction
└── knockout_stage_predict.md     # 5-step reasoning for knockout match prediction
```

## football-server/ — Backend (NOT YET IMPLEMENTED)

```
football-server/
└── REQUIREMENTS.md               # Backend spec (empty directory otherwise)
```
