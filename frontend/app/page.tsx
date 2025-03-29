import { getAllPapers } from "@/lib/api"
import PaperGrid from "@/components/paper-grid"
import { Suspense } from "react"
import Loading from "@/components/loading"
import FilterToggle from "../components/filter-toggle"

// Set cache control headers for this route
// Cache for 12 hours, revalidate every hour
export const revalidate = 3600 // 1 hour in seconds

export default async function Home({
  searchParams,
}: {
  searchParams?: { highlight?: string }
}) {
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-heading font-semibold text-gray-900">Papers</h2>
          <Suspense fallback={<div>Loading filter...</div>}>
            <FilterPapersToggle />
          </Suspense>
        </div>
        <Suspense fallback={<Loading />}>
          <AllPapers searchParams={searchParams} />
        </Suspense>
      </div>
    </div>
  )
}

function FilterPapersToggle() {
  return <FilterToggle />
}

async function AllPapers({ searchParams }: { searchParams?: { highlight?: string } }) {
  const allPapers = await getAllPapers()
  
  // Sort papers by date (newest first)
  const sortedPapers = [...allPapers].sort((a, b) => {
    if (!a.submitted_date) return 1 // Papers without dates go to the end
    if (!b.submitted_date) return -1
    
    const dateA = new Date(a.submitted_date)
    const dateB = new Date(b.submitted_date)
    
    return dateB.getTime() - dateA.getTime() // Descending order (newest first)
  })
  
  // Filter papers if highlight is true
  const { highlight } = await searchParams || {};
  const showOnlyHighlighted = highlight === "true"
  const filteredPapers = showOnlyHighlighted 
    ? sortedPapers.filter(paper => paper.highlight) 
    : sortedPapers
  
  return <PaperGrid papers={filteredPapers} />
}

