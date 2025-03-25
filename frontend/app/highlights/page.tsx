import { getHighlightedPapers } from "@/lib/api"
import PaperGrid from "@/components/paper-grid"
import { Suspense } from "react"
import Loading from "@/components/loading"

// Set cache control headers for this route
// Cache for 12 hours, revalidate every hour
export const revalidate = 3600 // 1 hour in seconds

export default function HighlightsPage() {
  return (
    <div className="bg-white">
      <div className="py-8 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-heading font-bold text-center text-gray-900 mb-4">Highlighted Papers</h1>
          <p className="text-lg text-gray-600 text-center max-w-3xl mx-auto">
            Featured research papers on AI safety and alignment
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Suspense fallback={<Loading />}>
          <HighlightedPapersGrid />
        </Suspense>
      </div>
    </div>
  )
}

// Separate component for data fetching
async function HighlightedPapersGrid() {
  const highlightedPapers = await getHighlightedPapers()
  return <PaperGrid papers={highlightedPapers} />
}

