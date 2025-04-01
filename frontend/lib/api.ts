import { API_BASE_URL, USE_MOCK_DATA } from "./config";
import { mockPaperDetails, mockPapers } from "./mock-data";
import type { PaperDetail, PaperSummary } from "./types";

/**
 * Fetches all papers from the API or returns mock data if API_BASE_URL is not set
 */
export async function getAllPapers(): Promise<PaperSummary[]> {
  if (USE_MOCK_DATA) {
    // Use mock data if API_BASE_URL is not available
    return mockPapers
  }

  try {
    const response = await fetch(`${API_BASE_URL}/papers`, {
      cache: "force-cache",
      next: {
        // revalidate every day
        revalidate: 86400,
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("Error fetching papers:", error)

    // Fallback to mock data in case of error
    return mockPapers
  }
}

/**
 * Fetches highlighted papers from the API or filters mock data if API_BASE_URL is not set
 */
export async function getHighlightedPapers(): Promise<PaperSummary[]> {
  if (USE_MOCK_DATA) {
    // Filter mock data for highlighted papers
    return mockPapers.filter((paper) => paper.highlight)
  }

  try {
    // Option 1: If the API has a dedicated endpoint for highlighted papers
    const response = await fetch(`${API_BASE_URL}/papers?highlight=true`)

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("Error fetching highlighted papers:", error)

    // Fallback to filtering mock data in case of error
    return mockPapers.filter((paper) => paper.highlight)
  }
}

/**
 * Fetches a specific paper by ID from the API or returns mock data if API_BASE_URL is not set
 */
export async function getPaperById(paperId: string): Promise<PaperDetail | null> {
  if (USE_MOCK_DATA) {
    // Use mock data if API_BASE_URL is not available
    const paper = mockPaperDetails[paperId]
    if (!paper) {
      console.warn(`Paper with ID ${paperId} not found in mock data`)
      return null
    }
    return paper
  }

  try {
    // Fetch from real API - FIXED: using "papers" (plural) instead of "paper" (singular)
    const response = await fetch(
      `${API_BASE_URL}/papers/${paperId}`,
      { cache: "force-cache" }
    )

    console.log(`Fetching paper from: ${API_BASE_URL}/papers/${paperId}`)

    if (response.status === 404) {
      console.warn(`Paper with ID ${paperId} not found in API`)
      return null
    }

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const data = await response.json()
    console.log("API response data:", data)

    // Ensure the data has all required fields
    return {
      ...data,
      // Ensure these arrays exist even if they're not in the API response
      tags: data.tags || [],
      figures: data.figures || [],
      // Ensure other required fields have default values if missing
      abstract: data.abstract || "No abstract available",
      tldr: data.tldr || "No summary available",
      summary: data.summary || "No detailed summary available",
      thumbnail_url: data.thumbnail_url || "/placeholder.svg?height=200&width=300",
      highlight: !!data.highlight,
    }
  } catch (error) {
    console.error(`Error fetching paper ${paperId}:`, error)

    // Fallback to mock data in case of error
    const paper = mockPaperDetails[paperId]
    if (!paper) {
      console.warn(`Paper with ID ${paperId} not found in mock data (fallback)`)
      return null
    }
    return paper
  }
}

