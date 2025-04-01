import { getPaperById } from "@/lib/api"
import { notFound } from "next/navigation"
import Link from "next/link"
import { Suspense } from "react"
import Loading from "@/components/loading"
import { API_BASE_URL, USE_MOCK_DATA } from "@/lib/config"
import SimpleHTMLMarkdown from "@/components/simple-html-markdown"
import PaperLayout from "@/components/paper-layout"
import { formatAuthors, formatDateFriendly, addOrdinalSuffix } from "@/lib/utils"
import ExpandableFigure from "@/components/expandable-figure"
import type { Metadata, ResolvingMetadata } from 'next'

// Set cache control headers for this route
// Cache for 12 hours, revalidate every hour
export const revalidate = 3600 // 1 hour in seconds

interface PaperPageProps {
  params: {
    paperId: string
  }
}

// Generate metadata for the page
export async function generateMetadata(
  { params }: PaperPageProps,
  parent: ResolvingMetadata
): Promise<Metadata> {
  const paperId = params.paperId
  const siteUrl = "https://papers.afspies.com" // Your site URL

  try {
    const paper = await getPaperById(paperId)

    if (!paper) {
      // Return default metadata or handle not found scenario appropriately
      // Returning basic metadata to avoid errors, but ideally should align with notFound behavior
      return {
        title: 'Paper Not Found',
        description: 'The requested paper could not be found.',
      }
    }

    // Optional: Get parent metadata if needed
    // const previousImages = (await parent).openGraph?.images || []

    // Limit description length for SEO
    const description = paper.abstract?.substring(0, 160) + (paper.abstract?.length > 160 ? '...' : '') || 'No abstract available.';
    
    // Determine the Open Graph image URL
    // Use the paper's thumbnail if it's an absolute URL, otherwise fallback to placeholder.jpg
    let imageUrl = `${siteUrl}/placeholder.jpg`; // Default fallback
    if (paper.thumbnail_url && (paper.thumbnail_url.startsWith('http://') || paper.thumbnail_url.startsWith('https://'))) {
      imageUrl = paper.thumbnail_url;
    } else if (paper.thumbnail_url) {
      // Optional: Handle relative URLs if you know the base path, but safer to use fallback for OG tags.
      console.warn(`Paper ${paper.uid} thumbnail_url (${paper.thumbnail_url}) is not absolute. Using fallback for Open Graph.`);
    }

    return {
      title: `${paper.title} | AI Safety Papers`,
      description: description,
      authors: paper.authors ? paper.authors.map(name => ({ name })) : undefined,
      keywords: paper.tags,
      openGraph: {
        title: paper.title,
        description: description,
        url: `${siteUrl}/paper/${paper.uid}`, // Use paper.uid here
        siteName: 'AI Safety Papers',
        images: [
          {
            url: imageUrl, // Use determined image URL
            width: 1200, // Standard OG image width
            height: 630, // Standard OG image height
          },
        ],
        locale: 'en_US',
        type: 'article',
        publishedTime: paper.submitted_date ? new Date(paper.submitted_date).toISOString() : undefined,
      },
      twitter: {
        card: 'summary_large_image',
        title: paper.title,
        description: description,
        // Twitter uses og:image by default if not specified. 
        // Add images: [imageUrl] here if you need a specific Twitter image.
      },
    }
  } catch (error) {
    console.error("Error generating metadata for paper:", paperId, error)
    // Return default metadata in case of error
    return {
      title: 'Error Loading Paper | AI Safety Papers',
      description: 'Could not load metadata for this paper.',
    }
  }
}

export default async function PaperPage({ params }: PaperPageProps) {
  // Make params awaitable
  const { paperId } = await params;
  return (
    <div className="bg-white">
      <Suspense fallback={<Loading />}>
        <PaperLayout>
          <PaperContent paperId={paperId} />
        </PaperLayout>
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
          const month = dateObj.toLocaleDateString('en-US', { month: 'long' });
          const day = dateObj.getDate();
          const year = dateObj.getFullYear();
          formattedDate = `${month} ${addOrdinalSuffix(day)}, ${year}`;
        }
      } catch (e) {
        console.error("Error formatting date:", e)
      }
    }

    // Format added date with friendly format
    const addedDate = (paper as any).added_date ? 
      formatDateFriendly((paper as any).added_date) : 
      "March 16th, 2025";

    return (
      <article className="font-serif">
        {/* Paper title and tags */}
        <header className="mb-8">
          <h1 className="paper-title text-2xl md:text-3xl font-bold mb-4">{paper.title}</h1>
        </header>

        {/* Academic paper style layout with two columns */}
        <div className="border-t border-b border-gray-300 py-6">
          <div className="flex flex-col md:flex-row">
            {/* Left column - Authors and Abstract */}
            <div className="md:w-2/3 md:pr-8">
              <h2 id="authors" data-toc-exclude="true" className="text-xl font-semibold mb-3 pb-2 border-b border-gray-200">Authors</h2>
              <div className="paper-authors mb-6">
                {paper.authors && paper.authors.length > 0 ? (
                  <p className="text-gray-800 leading-relaxed">
                    {paper.authors.join(", ")}
                  </p>
                ) : (
                  <p className="text-gray-800">Unknown Author</p>
                )}
              </div>
              
              <h2 id="abstract" className="text-xl font-semibold mb-3 pb-2 border-b border-gray-200">Abstract</h2>
              <p className="text-gray-600 text-sm leading-snug">{paper.abstract}</p>
            </div>
            
            {/* Right column - Publication Details */}
            <div className="md:w-1/3 md:pl-8 mt-6 md:mt-0">
              <h2 id="publication-details" data-toc-exclude="true" className="text-xl font-semibold mb-3 pb-2 border-b border-gray-200">Publication Details</h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-700" data-toc-exclude="true">Published:</h3>
                  <p>{formattedDate !== "Unknown date" ? formattedDate : "Unknown"}</p>
                </div>
                
                {paper.venue && (
                  <div>
                    <h3 className="font-semibold text-gray-700" data-toc-exclude="true">Venue:</h3>
                    <p>{paper.venue}</p>
                  </div>
                )}
                
                <div>
                  <h3 className="font-semibold text-gray-700" data-toc-exclude="true">Added to AI Safety Papers:</h3>
                  <p>{addedDate}</p>
                </div>
              </div>
              
              {/* Metadata section */}
              <h2 id="metadata" data-toc-exclude="true" className="text-xl font-semibold mb-3 pb-2 border-b border-gray-200 mt-6">Metadata</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-700" data-toc-exclude="true">Tags:</h3>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {paper.tags && paper.tags.length > 0 ? (
                      paper.tags.map((tag) => (
                        <span key={tag} className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                          {tag}
                        </span>
                      ))
                    ) : (
                      <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                        Uncategorized
                      </span>
                    )}
                  </div>
                </div>
                
                {paper.url && (
                  <div>
                    <h3 className="font-semibold text-gray-700" data-toc-exclude="true">Original Paper:</h3>
                    <a 
                      href={paper.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      Link
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="mt-8">
          {paper.summary && (
            <section className="mb-10">
              <h2 id="summary" className="paper-section-title text-xl font-bold mb-4 border-b border-gray-200 pb-2">Summary</h2>
              <div className="paper-content leading-snug">
                <SimpleHTMLMarkdown 
                  content={paper.summary} 
                  className="leading-tight" 
                  figures={paper.figures} 
                />
              </div>
            </section>
          )}

          <div className="mt-10 pt-4 border-t border-gray-200">
            <Link href="/" className="text-blue-600 hover:text-blue-800 transition-colors">
              ← Back to papers
            </Link>
          </div>
        </div>
      </article>
    )
  } catch (error) {
    console.error("Error in PaperContent:", error)
    notFound()
  }
}

