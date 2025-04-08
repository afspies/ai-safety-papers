import { MetadataRoute } from 'next'

const siteUrl = 'https://www.aisafetypapers.org'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*', // Applies to all crawlers
      allow: '/', // Allow crawling of all content by default
      // Add disallow rules here if needed, e.g.:
      // disallow: '/admin/', 
      // disallow: '/private/',
    },
    sitemap: `${siteUrl}/sitemap.xml`, // Point crawlers to the sitemap
  }
} 