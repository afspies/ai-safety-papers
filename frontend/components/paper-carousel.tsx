"use client"

import type { PaperSummary } from "@/lib/types"
import { useState, useEffect, useRef } from "react"
import Link from "next/link"
import Image from "next/image"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { useCarousel } from "@/hooks/use-carousel"

interface PaperCarouselProps {
  papers: PaperSummary[]
}

export default function PaperCarousel({ papers }: PaperCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isClient, setIsClient] = useState(false)
  const { visibleCards } = useCarousel()
  const carouselRef = useRef<HTMLDivElement>(null)

  // Set isClient to true once component mounts
  useEffect(() => {
    setIsClient(true)
  }, [])

  useEffect(() => {
    if (!isClient) return

    const interval = setInterval(() => {
      nextSlide()
    }, 5000)

    return () => clearInterval(interval)
  }, [currentIndex, isClient, papers.length])

  // If not client-side yet, render a static version
  if (!isClient || papers.length === 0) {
    return (
      <div className="relative w-full py-16 flex items-center justify-center">
        <div className="text-gray-600 text-xl font-heading">Loading featured papers...</div>
      </div>
    )
  }

  const nextSlide = () => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % papers.length)
  }

  const prevSlide = () => {
    setCurrentIndex((prevIndex) => (prevIndex - 1 + papers.length) % papers.length)
  }

  // Calculate which papers to show based on current index
  const getVisiblePapers = () => {
    const visiblePapers = []
    for (let i = 0; i < papers.length; i++) {
      // Calculate position relative to currentIndex
      const position = (i - currentIndex + papers.length) % papers.length
      if (position < visibleCards) {
        visiblePapers.push({
          paper: papers[i],
          position,
        })
      }
    }
    return visiblePapers
  }

  const visiblePapers = getVisiblePapers()

  return (
    <div className="relative w-full py-16 border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-2xl font-heading font-semibold mb-8 text-center">Featured Papers</h2>

        <div className="relative">
          {/* Carousel container */}
          <div ref={carouselRef} className="flex justify-center items-stretch overflow-hidden py-4" aria-live="polite">
            <div className="flex space-x-6 transition-transform duration-500 ease-in-out">
              {visiblePapers.map(({ paper, position }) => (
                <div
                  key={paper.uid}
                  className={`
                    carousel-card flex-shrink-0 w-full sm:w-80 md:w-96
                    ${
                      position === 0
                        ? "scale-100 opacity-100 z-20"
                        : position === 1
                          ? "scale-95 opacity-90 z-10 translate-x-4"
                          : "scale-90 opacity-80 z-0 translate-x-8"
                    }
                  `}
                  style={{
                    transform: `translateX(${position * -5}%)`,
                  }}
                >
                  <Link href={`/paper/${paper.uid}`}>
                    <div className="bg-white rounded-lg shadow-md border border-gray-100 overflow-hidden h-full hover:shadow-lg transition-shadow duration-300">
                      <div className="relative h-48 w-full bg-gray-50 flex items-center justify-center">
                        <Image
                          src={paper.thumbnail_url || "/placeholder.svg"}
                          alt={paper.title}
                          fill
                          className="object-contain p-2"
                        />
                      </div>
                      <div className="p-4">
                        <h3 className="text-lg font-heading font-semibold line-clamp-2">{paper.title}</h3>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-1">{paper.authors.join(", ")}</p>
                        <p className="text-sm text-gray-700 mt-2 line-clamp-2">{paper.tldr}</p>
                        {paper.highlight && (
                          <span className="inline-block bg-yellow-50 text-yellow-800 text-xs px-2 py-1 rounded mt-2 font-medium">
                            Highlighted
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>
                </div>
              ))}
            </div>
          </div>

          {/* Navigation buttons */}
          <button
            onClick={prevSlide}
            className="absolute left-0 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 rounded-full p-2 shadow-md z-30 transition-all duration-200 hover:scale-110"
            aria-label="Previous paper"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>

          <button
            onClick={nextSlide}
            className="absolute right-0 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white text-gray-800 rounded-full p-2 shadow-md z-30 transition-all duration-200 hover:scale-110"
            aria-label="Next paper"
          >
            <ChevronRight className="h-6 w-6" />
          </button>
        </div>

        {/* Pagination dots */}
        <div className="flex justify-center mt-6 space-x-2">
          {papers.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                index === currentIndex ? "bg-blue-600 w-5" : "bg-gray-300 hover:bg-gray-400"
              }`}
              aria-label={`Go to slide ${index + 1}`}
              aria-current={index === currentIndex ? "true" : "false"}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

