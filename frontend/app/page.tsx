import { getAllPapers } from "@/lib/api"
import PaperGrid from "@/components/paper-grid"
import { Suspense } from "react"
import Loading from "@/components/loading"
import FilterToggle from "../components/filter-toggle"
import SearchIcon from "@/components/search-icon"
import { filterPapersByQuery } from "@/lib/search"

// Set cache control headers for this route
// Cache for 12 hours, revalidate every hour
export const revalidate = 3600 // 1 hour in seconds

export default async function Home({
  searchParams,
}: {
  searchParams?: { highlight?: string; q?: string }
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
        {/* Responsive header section */}
        <div className="mb-8">
          {/* Mobile: Title and filter on same line, search below */}
          <div className="md:hidden">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-heading font-semibold text-gray-900">Papers</h2>
              <Suspense fallback={<div>Loading filter...</div>}>
                <FilterPapersToggle />
              </Suspense>
            </div>
            <div className="w-full">
              <Suspense fallback={<div>Loading search...</div>}>
                <SearchTools />
              </Suspense>
            </div>
          </div>
          
          {/* Desktop: Title on left, search and filter on right */}
          <div className="hidden md:flex md:justify-between md:items-center">
            <h2 className="text-2xl font-heading font-semibold text-gray-900">Papers</h2>
            <div className="flex items-center space-x-4">
              <Suspense fallback={<div>Loading search...</div>}>
                <SearchTools />
              </Suspense>
              <Suspense fallback={<div>Loading filter...</div>}>
                <FilterPapersToggle />
              </Suspense>
            </div>
          </div>
        </div>
        
        <Suspense fallback={<Loading />}>
          <AllPapers searchParams={searchParams} />
        </Suspense>
      </div>
    </div>
  )
}

function SearchTools() {
  return <SearchIcon />
}

function FilterPapersToggle() {
  return <FilterToggle />
}

async function AllPapers({ searchParams }: { searchParams?: { highlight?: string; q?: string } }) {
  const allPapers = await getAllPapers()
  
  // Sort papers by date (newest first)
  const sortedPapers = [...allPapers].sort((a, b) => {
    if (!a.submitted_date) return 1 // Papers without dates go to the end
    if (!b.submitted_date) return -1
    
    const dateA = new Date(a.submitted_date)
    const dateB = new Date(b.submitted_date)
    
    return dateB.getTime() - dateA.getTime() // Descending order (newest first)
  })
  
  // Get search query from URL params - await the searchParams object
  const params = await searchParams || {};
  const { highlight, q } = params;
  const searchQuery = q || '';
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

