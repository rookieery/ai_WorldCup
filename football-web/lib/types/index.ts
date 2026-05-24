/**
 * Unified type re-exports.
 *
 * Import from `@/lib/types` to access any shared type.
 */

export type {
  Team,
  TeamDetail,
  TeamStanding,
} from "./team"

export type {
  Match,
  MatchStatus,
  MatchEvent,
  MatchEventType,
  MatchQueryParams,
  CityIcon,
} from "./match"

export type {
  BracketTeam,
  BracketMatch,
  BracketRound,
  BracketTree,
  BracketRoundName,
  BracketMatchStatus,
} from "./bracket"

export type {
  Message,
  MessageRole,
  MessageType,
  TeamAnalysis,
  TeamAnalysisSide,
  TeamStats,
  SSEEvent,
  SSEEventType,
} from "./ai"

export type {
  ApiResponse,
  PaginatedResponse,
  ApiError,
} from "./api"
