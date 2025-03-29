"use client"

import { ReactNode, useEffect, useState } from "react"
import TableOfContents from "./table-of-contents"

interface PaperLayoutProps {
  children: ReactNode
}

export default function PaperLayout({ children }: PaperLayoutProps) {
  const [showToc, setShowToc] = useState(false)

  // Only show TOC after hydration to prevent SSR issues
  useEffect(() => {
    setShowToc(true)
  }, [])

  return (
    <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="lg:flex lg:gap-12">
        {/* Floating TOC sidebar */}
        {showToc && (
          <div className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pr-4 pb-10 overscroll-contain scrollbar-thin scrollbar-thumb-gray-200 scrollbar-track-transparent">
              <TableOfContents className="pb-10" />
            </div>
          </div>
        )}
        
        {/* Main content wrapper */}
        <div className="flex-1">
          <div className="max-w-3xl">
            {children}
          </div>
        </div>
      </div>
      
      {/* Mobile TOC button */}
      {showToc && (
        <div className="lg:hidden fixed bottom-6 right-6 z-50">
          <TocMobileButton />
        </div>
      )}
    </div>
  )
}

// Mobile TOC button component
function TocMobileButton() {
  const [isOpen, setIsOpen] = useState(false)
  
  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center"
        aria-label="Table of Contents"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
      
      {isOpen && (
        <div className="fixed inset-0 bg-black/20 z-50" onClick={() => setIsOpen(false)}>
          <div 
            className="absolute right-0 top-0 bottom-0 w-64 bg-white shadow-xl p-4 transform transition-transform"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <button onClick={() => setIsOpen(false)} aria-label="Close menu" className="p-1 rounded-full hover:bg-gray-100">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <TableOfContents />
          </div>
        </div>
      )}
    </>
  )
} 