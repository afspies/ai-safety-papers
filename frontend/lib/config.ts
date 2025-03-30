/**
 * Configuration settings for the application
 */

// API configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || ""

// Feature flags
export const USE_MOCK_DATA = !API_BASE_URL

// Logging
export const isDevelopment = process.env.NODE_ENV === "development"

// Log configuration on startup in development
if (isDevelopment) {
  console.log("App Configuration:", {
    API_BASE_URL: API_BASE_URL || "(not set, using mock data)",
    USE_MOCK_DATA,
    NODE_ENV: process.env.NODE_ENV,
  })
}

