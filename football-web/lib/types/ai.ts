/**
 * Shared AI Copilot type definitions.
 *
 * `TeamStats` is the five-dimension radar stat shape.
 * `TeamAnalysisSide` groups one side's stats + win probability.
 * `TeamAnalysis` is the full two-team analysis payload.
 * `Message` represents a chat message in the AI panel.
 * `SSEEvent` describes the server-sent event format used for streaming AI responses.
 */

export interface TeamStats {
  attack: number
  defense: number
  possession: number
  setpieces: number
  form: number
}

export interface TeamAnalysisSide {
  name: string
  code?: string
  flag: string
  stats: TeamStats
  winProbability: number
}

export interface TeamAnalysis {
  team1: TeamAnalysisSide
  team2: TeamAnalysisSide
  drawProbability: number
  keyInsights: string[]
}

export type MessageRole = "user" | "assistant"
export type MessageType = "text" | "analysis" | "analysis-context"

export interface Message {
  id: number
  role: MessageRole
  content: string
  type?: MessageType
  analysisData?: TeamAnalysis
}

export type SSEEventType = "thinking" | "answer" | "analysis" | "done" | "error"

export interface SSEEvent {
  type: SSEEventType
  content?: string
  data?: TeamAnalysis
}
