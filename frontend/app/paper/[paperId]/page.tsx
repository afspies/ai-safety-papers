import { getPaperById } from "@/lib/api"
import { notFound } from "next/navigation"
import Link from "next/link"
import { Suspense } from "react"
import Loading from "@/components/loading"
import { API_BASE_URL, USE_MOCK_DATA } from "@/lib/config"
import SimpleHTMLMarkdown from "@/components/simple-html-markdown"
import ExpandableImage from "@/components/expandable-image"

// Set cache control headers for this route
// Cache for 12 hours, revalidate every hour
export const revalidate = 3600 // 1 hour in seconds

interface PaperPageProps {
  params: {
    paperId: string
  }
}

export default async function PaperPage({ params }: PaperPageProps) {
  // Make params awaitable
  const { paperId } = await params;
  return (
    <div className="bg-white">
      <Suspense fallback={<Loading />}>
        <PaperContent paperId={paperId} />
      </Suspense>
    </div>
  )
}

async function PaperContent({ paperId }: { paperId: string }) {
  try {
    console.log(`Fetching paper with ID: ${paperId}`)
    console.log(`API_BASE_URL: ${API_BASE_URL}`)
    console.log(`Using mock data: ${USE_MOCK_DATA}`)

    const paper = await getPaperById(paperId)

    if (!paper) {
      console.error(`Paper with ID ${paperId} not found`)
      notFound()
    }

    console.log(`Successfully fetched paper: ${paper.title}`)

    // Format the date on the server to avoid hydration mismatch
    // Handle the date in ISO format from the API
    let formattedDate = "Unknown date"
    if (paper.submitted_date) {
      try {
        // Handle both Date objects and ISO strings
        const dateObj = typeof paper.submitted_date === "string" ? new Date(paper.submitted_date) : paper.submitted_date

        if (!isNaN(dateObj.getTime())) {
          formattedDate = dateObj.toISOString().split("T")[0]
        }
      } catch (e) {
        console.error("Error formatting date:", e)
      }
    }

    return (
      <article className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-serif">
        {/* Paper header - Academic style */}
        <header className="mb-10 text-center">
          <div className="mb-4">
            {paper.tags && paper.tags.length > 0 ? (
              paper.tags.map((tag) => (
                <span key={tag} className="paper-tag">
                  {tag}
                </span>
              ))
            ) : (
              <span className="paper-tag">Uncategorized</span>
            )}
          </div>

          <h1 className="paper-title text-2xl md:text-3xl font-bold mb-4">{paper.title}</h1>

          <div className="paper-authors text-lg mb-2">
            {paper.authors && paper.authors.length > 0 ? (
              paper.authors.map((author, index) => (
                <span key={index}>
                  {index > 0 && ", "}
                  {author}
                </span>
              ))
            ) : (
              <span>Unknown Author</span>
            )}
          </div>

          <div className="paper-metadata text-sm text-gray-600 mb-6">
            {paper.venue && <span>{paper.venue}</span>}
            {paper.venue && formattedDate !== "Unknown date" && <span> • </span>}
            <span>{formattedDate}</span>
          </div>

          <div className="mt-6 max-w-4xl mx-auto border-t border-gray-200 pt-6">
            <h2 className="text-xl font-semibold mb-3">Abstract</h2>
            <p className="text-gray-700 leading-snug">{paper.abstract}</p>
          </div>
        </header>

        {/* Main content */}
        <div className="max-w-4xl mx-auto">
          {paper.summary && (
            <section className="mb-10">
              <h2 className="paper-section-title text-xl font-bold mb-4 border-b border-gray-200 pb-2">Summary</h2>
              <div className="paper-content leading-snug">
                <SimpleHTMLMarkdown content={paper.summary} className="leading-tight" />
              </div>
            </section>
          )}

          {paper.figures && paper.figures.length > 0 && (
            <section className="mb-10">
              <h2 className="paper-section-title text-xl font-bold mb-4 border-b border-gray-200 pb-2">Figures</h2>
              <div className="space-y-6 mt-4">
                {paper.figures.map((figure, index) => (
                  <figure key={figure.id || `fig-${index}`} className="bg-white border border-gray-200 rounded-md shadow-sm p-4">
                    <ExpandableImage
                      src={figure.url || "/placeholder.svg"}
                      alt={figure.caption || "Figure"}
                      className="mb-3"
                    />
                    <figcaption className="text-sm text-gray-700 text-center font-serif">
                      {figure.caption || "Figure"}
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>
          )}

          <div className="mt-10 pt-4 border-t border-gray-200 flex justify-between items-center">
            <Link href="/" className="text-blue-600 hover:text-blue-800 transition-colors">
              ← Back to papers
            </Link>
            {paper.url && (
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                View Original Paper
              </a>
            )}
          </div>
        </div>
      </article>
    )
  } catch (error) {
    console.error("Error in PaperContent:", error)
    notFound()
  }
}

