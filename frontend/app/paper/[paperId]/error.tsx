"use client"

import { useEffect } from "react"
import Link from "next/link"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error("Paper page error:", error)
  }, [error])

  // Check if it's a "not found" error
  const isNotFound = error.message?.includes("Not found") || error.message?.includes("NEXT_NOT_FOUND")

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4">
      <h2 className="text-2xl font-bold mb-4 text-center">
        {isNotFound ? "Paper Not Found" : "Something went wrong!"}
      </h2>
      <p className="text-gray-600 mb-6 text-center max-w-md">
        {isNotFound
          ? "The paper you're looking for doesn't exist or has been removed."
          : "We encountered an error while trying to load this paper. Please try again later."}
      </p>
      <div className="flex flex-col sm:flex-row gap-4">
        {!isNotFound && (
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Try again
          </button>
        )}
        <Link
          href="/"
          className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors text-center"
        >
          Go back home
        </Link>
      </div>
    </div>
  )
}

