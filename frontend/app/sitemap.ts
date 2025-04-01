import { MetadataRoute } from 'next'
import { getAllPapers } from '@/lib/api' // Assuming this function exists

const siteUrl = 'https://papers.afspies.com'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Fetch all papers to generate routes
  // TODO: Implement getAllPapers() in @/lib/api if it doesn't exist
  let papers = []
  try {
    // We only need the ID and maybe a last modified date if available
    // Adjust getAllPapers() accordingly if possible for performance
    papers = await getAllPapers() 
  } catch (error) {
    console.error("Failed to fetch papers for sitemap:", error);
    // Return a minimal sitemap even if fetching papers fails
    return [
      {
        url: siteUrl,
        lastModified: new Date(),
        changeFrequency: 'weekly',
        priority: 1,
      },
    ]
  }

  const paperEntries: MetadataRoute.Sitemap = papers.map((paper) => ({
    url: `${siteUrl}/paper/${paper.uid}`,
    // Use submitted_date if available, otherwise use current date
    lastModified: paper.submitted_date ? new Date(paper.submitted_date) : new Date(), 
    changeFrequency: 'monthly', // Or 'yearly' if papers rarely change
    priority: 0.8,
  }));

  return [
    {
      url: siteUrl,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 1,
    },
    ...paperEntries,
  ]
} 