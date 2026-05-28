/**
 * Shared API response type definitions.
 *
 * `ApiResponse<T>` is the standard envelope returned by all backend endpoints.
 * `PaginatedResponse<T>` extends it with pagination metadata.
 */

export interface ApiResponse<T> {
  code: number
  data: T
  message: string
}

export interface PaginatedResponse<T> extends ApiResponse<T> {
  data: T
  pagination: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

export interface ApiError {
  code: number
  message: string
  detail?: string
}
