/**
 * Venues API — getVenues.
 */

import { apiRequest, buildQueryString } from "@/lib/api-client"

// ── Types matching the backend VenueResponse VO ──────────────────────────────

interface Venue {
  id: number
  name: string
  city: string
  country: string
  timezone: string
  utc_offset: string
  capacity: number
}

interface VenuesListResponse {
  items: Venue[]
  total: number
  page: number
  page_size: number
}

// ── API functions ─────────────────────────────────────────────────────────────

interface GetVenuesParams {
  page?: number
  pageSize?: number
}

/**
 * Fetch a paginated list of host city venues.
 */
export async function getVenues(params: GetVenuesParams = {}): Promise<VenuesListResponse> {
  const query = buildQueryString({
    page: params.page,
    page_size: params.pageSize,
  })

  return apiRequest<VenuesListResponse>(`/api/venues${query}`)
}