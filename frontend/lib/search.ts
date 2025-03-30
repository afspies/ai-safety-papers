import type { PaperSummary } from "./types"

/**
 * Filter papers based on search query against title, abstract, and TLDR
 * 
 * @param papers The array of papers to filter
 * @param query The search query string
 * @returns Filtered array of papers that match the query
 */
export function filterPapersByQuery(papers: PaperSummary[], query: string): PaperSummary[] {
  if (!query || query.trim() === '') {
    return papers
  }
  
  const normalizedQuery = query.toLowerCase().trim()
  
  return papers.filter(paper => {
    const title = paper.title?.toLowerCase() || ''
    const abstract = paper.abstract?.toLowerCase() || ''
    const tldr = paper.tldr?.toLowerCase() || ''
    const authors = paper.authors?.join(' ').toLowerCase() || ''
    const tags = paper.tags?.join(' ').toLowerCase() || ''
    
    return (
      title.includes(normalizedQuery) ||
      abstract.includes(normalizedQuery) ||
      tldr.includes(normalizedQuery) ||
      authors.includes(normalizedQuery) ||
      tags.includes(normalizedQuery)
    )
  })
}

/**
 * Highlights the matched text in a string
 * 
 * @param text The text to highlight matches in
 * @param query The search query to highlight
 * @returns The text with HTML highlights
 */
export function highlightMatches(text: string, query: string): string {
  if (!query || query.trim() === '' || !text) {
    return text
  }
  
  const normalizedQuery = query.toLowerCase().trim()
  const normalizedText = text.toLowerCase()
  
  // Simple implementation for basic highlighting
  // This should be replaced with a more robust solution for production
  if (normalizedText.includes(normalizedQuery)) {
    const regex = new RegExp(normalizedQuery, 'gi')
    return text.replace(regex, match => `<mark class="bg-yellow-200 text-gray-900">${match}</mark>`)
  }
  
  return text
} 