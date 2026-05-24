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

## football-server/ — Backend (FastAPI + SQLite + Redis)

```
football-server/
├── pyproject.toml               # Project metadata + all core dependencies
├── alembic.ini                  # Alembic config (DB URL from app.config, logging)
├── .env.example                 # Environment variable templates
├── .gitignore                   # Python/venv/db ignore rules
├── alembic/
│   ├── env.py                   # Async migration runner (reads settings.DATABASE_URL)
│   ├── script.py.mako           # Migration script template
│   └── versions/
│       └── 001_initial_schema.py  # Initial migration: 5 tables + FK relationships
├── app/
│   ├── __init__.py              # Package init (empty)
│   ├── config.py                # Pydantic Settings: all env vars with defaults
│   ├── exceptions/
│   │   ├── __init__.py          # Re-exports all exception classes
│   │   └── exceptions.py        # AppException hierarchy (NotFound, Validation, Business, ExternalService)
│   ├── middleware/
│   │   ├── __init__.py          # Re-exports all middleware classes
│   │   ├── error_handler.py     # Global exception → ApiResponse {code, data, message} middleware
│   │   ├── cors.py              # CORS middleware (origins from config)
│   │   └── logging.py           # Request logging middleware (method/path/status/duration)
│   └── models/
│       ├── __init__.py          # Re-exports all model classes + Base
│       ├── base.py              # DeclarativeBase + TimestampMixin (created_at, updated_at)
│       ├── team.py              # Team model (48 teams, code/name UNIQUE)
│       ├── venue.py             # Venue model (16 stadiums with timezone info)
│       ├── match.py             # Match model (104 fixtures, FK→Team/Venue/self)
│       ├── group_standing.py    # GroupStanding model (48 rows, FK→Team UNIQUE)
│       └── match_event.py       # MatchEvent model (goals/cards/subs, FK→Match)
└── scalable-beaming-riddle.md   # Backend architecture plan
```
