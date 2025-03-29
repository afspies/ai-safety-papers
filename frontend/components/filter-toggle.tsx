"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"

export default function FilterToggle() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // Get the current highlight filter state from URL
  const [isHighlighted, setIsHighlighted] = useState<boolean>(
    searchParams?.get("highlight") === "true"
  )

  // Update URL when toggle changes
  const handleToggle = () => {
    const newValue = !isHighlighted
    setIsHighlighted(newValue)
    
    // Create new URL with updated params
    const params = new URLSearchParams(searchParams?.toString())
    if (newValue) {
      params.set("highlight", "true")
    } else {
      params.delete("highlight")
    }
    
    // Update the URL without refreshing the page
    router.push(`/?${params.toString()}`)
  }
  
  return (
    <div className="flex items-center">
      <span className="mr-3 text-sm font-medium text-gray-700">
        {isHighlighted ? "Showing highlighted papers" : "Showing all papers"}
      </span>
      <button
        type="button"
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          isHighlighted ? "bg-blue-600" : "bg-gray-200"
        }`}
        role="switch"
        aria-checked={isHighlighted}
        onClick={handleToggle}
      >
        <span className="sr-only">Highlight filter</span>
        <span
          aria-hidden="true"
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            isHighlighted ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
      <span className="ml-3 text-sm font-medium text-gray-700">
        Highlights only
      </span>
    </div>
  )
} 