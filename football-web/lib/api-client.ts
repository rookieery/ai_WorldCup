/**
 * Core API client — fetch wrapper with unified error handling.
 *
 * - Automatically prepends `NEXT_PUBLIC_API_URL` to every request.
 * - Attaches `Accept-Language` header based on current i18n state.
 * - Unwraps the backend `ApiResponse<T>` envelope, throwing on non-success.
 * - Provides `buildQueryString()` for serializing query parameters.
 */

import type { ApiResponse, ApiError } from "@/lib/types/api"

// ── Configuration ────────────────────────────────────────────────────────────

const BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const DEFAULT_TIMEOUT_MS = 15_000

// ── Language helper ──────────────────────────────────────────────────────────

let currentLang = "en"

/**
 * Update the language used in the `Accept-Language` header.
 * Called by the i18n provider whenever the user switches language.
 */
export function setApiClientLanguage(lang: string): void {
  currentLang = lang
}

/**
 * Read the current API client language.
 * Useful when constructing manual queries that need the `lang` param.
 */
export function getApiClientLanguage(): string {
  return currentLang
}

// ── Error types ──────────────────────────────────────────────────────────────

export class ApiClientError extends Error {
  public readonly code: number
  public readonly detail?: string

  constructor(code: number, message: string, detail?: string) {
    super(message)
    this.name = "ApiClientError"
    this.code = code
    this.detail = detail
  }
}

// ── Query-string builder ─────────────────────────────────────────────────────

/**
 * Serialise a flat key-value object into a URL query string.
 * - `undefined` / `null` values are skipped.
 * - Arrays are comma-joined.
 * - Returns `""` when no valid entries remain.
 */
export function buildQueryString(
  params?: Record<string, string | number | boolean | undefined> | undefined,
): string {
  if (!params) return ""

  const entries = Object.entries(params).filter(
    (entry): entry is [string, string | number | boolean] =>
      entry[1] !== undefined && entry[1] !== null,
  )

  if (entries.length === 0) return ""

  const searchParams = new URLSearchParams(
    entries.map(([key, value]) => [key, String(value)]),
  )

  return `?${searchParams.toString()}`
}

// ── Core request helper ──────────────────────────────────────────────────────

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH"
  body?: unknown
  headers?: Record<string, string>
  timeout?: number
}

/**
 * Perform an authenticated, language-aware fetch and unwrap `ApiResponse<T>`.
 *
 * @throws {ApiClientError} when the network request fails or the backend
 *                          returns a non-success `ApiResponse` envelope.
 */
export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, headers = {}, timeout = DEFAULT_TIMEOUT_MS } = options

  const url = `${BASE_URL}${path}`

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  const fetchHeaders: Record<string, string> = {
    "Accept": "application/json",
    "Accept-Language": currentLang,
    ...headers,
  }

  if (body !== undefined) {
    fetchHeaders["Content-Type"] = "application/json"
  }

  let response: Response

  try {
    response = await fetch(url, {
      method,
      headers: fetchHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiClientError(408, "Request timed out. Please try again.")
    }
    throw new ApiClientError(
      0,
      "Unable to connect to the server. Please check your network connection.",
    )
  } finally {
    clearTimeout(timeoutId)
  }

  // ── Non-2xx status codes ────────────────────────────────────────────────

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`
    let errorDetail: string | undefined

    try {
      const errorBody = (await response.json()) as ApiError
      if (errorBody.message) {
        errorMessage = errorBody.message
      }
      errorDetail = errorBody.detail
    } catch {
      // Response body was not JSON — keep default message
    }

    switch (response.status) {
      case 401:
        throw new ApiClientError(401, "Authentication required.", errorDetail)
      case 403:
        throw new ApiClientError(403, "You do not have permission to perform this action.", errorDetail)
      case 404:
        throw new ApiClientError(404, "The requested resource was not found.", errorDetail)
      case 422:
        throw new ApiClientError(422, errorMessage || "Invalid request data.", errorDetail)
      case 429:
        throw new ApiClientError(429, "Too many requests. Please wait a moment and try again.", errorDetail)
      case 500:
        throw new ApiClientError(500, "Server error. Please try again later.", errorDetail)
      case 502:
      case 503:
      case 504:
        throw new ApiClientError(response.status, "Service temporarily unavailable. Please try again later.", errorDetail)
      default:
        throw new ApiClientError(response.status, errorMessage, errorDetail)
    }
  }

  // ── Unwrap ApiResponse<T> envelope ──────────────────────────────────────

  const json = (await response.json()) as ApiResponse<T>

  // The backend returns `{ code, data, message }`.
  // For successful requests code is always 200 but we guard anyway.
  if (json.code !== 200 && json.code !== undefined) {
    throw new ApiClientError(json.code, json.message || "Unknown API error")
  }

  return json.data as T
}