import { getAllPapers, getHighlightedPapers } from "@/lib/api"
import PaperCarousel from "@/components/paper-carousel"
import PaperGrid from "@/components/paper-grid"
import { Suspense } from "react"
import Loading from "@/components/loading"

// Set cache control headers for this route
// Cache for 12 hours, revalidate every hour
export const revalidate = 3600 // 1 hour in seconds

export default async function Home() {
  return (
    <div className="bg-white">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-heading font-bold text-center text-gray-900 mb-4">AI Safety Papers</h1>
          <p className="text-xl text-gray-600 text-center max-w-3xl mx-auto">
            A collection of important research papers on AI safety and alignment
          </p>
        </div>
      </div>

      <Suspense fallback={<Loading />}>
        <FeaturedPapers />
      </Suspense>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="text-2xl font-heading font-semibold mb-8 text-gray-900">All Papers</h2>
        <Suspense fallback={<Loading />}>
          <AllPapers />
        </Suspense>
      </div>
    </div>
  )
}

// Separate components for data fetching
async function FeaturedPapers() {
  const highlightedPapers = await getHighlightedPapers()
  return <PaperCarousel papers={highlightedPapers} />
}

async function AllPapers() {
  const allPapers = await getAllPapers()
  return <PaperGrid papers={allPapers} />
}

