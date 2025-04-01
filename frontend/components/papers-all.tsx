"use client"

import PaperGrid from "@/components/paper-grid"
import { filterPapersByQuery } from "@/lib/search"
import { PaperSummary } from "@/lib/types"
import { useSearchParams } from "next/navigation"

interface AllPapersProps {
  papers: PaperSummary[]
}


export function AllPapers({ papers: allPapers }: AllPapersProps) {
  const searchParams = useSearchParams()

  // Sort papers by date (newest first)
  const sortedPapers = [...allPapers].sort((a, b) => {
    if (!a.submitted_date) return 1 // Papers without dates go to the end
    if (!b.submitted_date) return -1

    const dateA = new Date(a.submitted_date)
    const dateB = new Date(b.submitted_date)

    return dateB.getTime() - dateA.getTime() // Descending order (newest first)
  })

  // Get search query from URL params - await the searchParams object
  const highlight = searchParams?.get("highlight")
  const searchQuery = searchParams?.get("q") || ''
  const showOnlyHighlighted = highlight === "true"

  // Apply filters: first filter by highlight if needed, then by search query
  let filteredPapers = showOnlyHighlighted
    ? sortedPapers.filter(paper => paper.highlight)
    : sortedPapers

  // Apply search filtering if query exists
  if (searchQuery) {
    filteredPapers = filterPapersByQuery(filteredPapers, searchQuery)
  }

  // Show search results info if search was performed
  const searchInfo = searchQuery ? (
    <div className="mb-6 text-gray-600">
      Found {filteredPapers.length} paper{filteredPapers.length !== 1 ? 's' : ''}
      for "<span className="font-medium">{searchQuery}</span>"
      {showOnlyHighlighted ? " (highlights only)" : ""}
    </div>
  ) : null

  return (
    <>
      {searchInfo}
      <PaperGrid papers={filteredPapers} />
      {filteredPapers.length === 0 && !searchQuery && (
        <div className="text-center py-12 text-gray-500">
          No papers available.
        </div>
      )}
      {filteredPapers.length === 0 && searchQuery && (
        <div className="text-center py-12 text-gray-500">
          No matching papers found. Try a different search term.
        </div>
      )}
    </>
  )
}

