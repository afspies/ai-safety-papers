"use client"

import type { PaperSummary } from "@/lib/types"
import Link from "next/link"
import { useState, useEffect, useRef, createContext, useContext } from "react"
import Image from "next/image"
import { formatAuthors, formatDateFriendly, cn } from "@/lib/utils"

// Create context for tracking global hover state
const HoverContext = createContext<{
  hoveredId: string | null;
  setHoveredId: (id: string | null) => void;
}>({
  hoveredId: null,
  setHoveredId: () => {},
});

export function PaperCardProvider({ children }: { children: React.ReactNode }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  return (
    <HoverContext.Provider value={{ hoveredId, setHoveredId }}>
      {children}
    </HoverContext.Provider>
  );
}

interface PaperCardProps {
  paper: PaperSummary
}

export default function PaperCard({ paper }: PaperCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [isMounted, setIsMounted] = useState(false)
  const [showTopShadow, setShowTopShadow] = useState(false)
  const [showBottomShadow, setShowBottomShadow] = useState(true)
  const [imageError, setImageError] = useState(false)
  const contentRef = useRef<HTMLDivElement>(null)
  
  // Get hover context if available (will be undefined if not wrapped in provider)
  const hoverContext = useContext(HoverContext);

  // Format the date directly here with compact option
  const formattedDate = paper.submitted_date ? formatDateFriendly(paper.submitted_date, true) : "";
  
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Handle scroll shadows
  const handleScroll = () => {
    if (!contentRef.current) return
    
    const { scrollTop, scrollHeight, clientHeight } = contentRef.current
    setShowTopShadow(scrollTop > 10)
    setShowBottomShadow(scrollTop + clientHeight < scrollHeight - 10)
  }

  useEffect(() => {
    if (contentRef.current) {
      handleScroll()
      contentRef.current.addEventListener('scroll', handleScroll)
    }
    
    return () => {
      if (contentRef.current) {
        contentRef.current.removeEventListener('scroll', handleScroll)
      }
    }
  }, [isHovered, imageError])

  // Handle image error
  const handleImageError = () => {
    setImageError(true)
  }

  // Handle mouse enter/leave
  const handleMouseEnter = () => {
    setIsHovered(true)
    if (hoverContext) {
      hoverContext.setHoveredId(paper.uid)
    }
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
    if (hoverContext) {
      hoverContext.setHoveredId(null)
    }
  }

  // Determine if this card should be grayed out
  const isGrayedOut = hoverContext?.hoveredId !== null && hoverContext?.hoveredId !== paper.uid

  if (!isMounted) {
    return (
      <div className={cn(
        "bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden relative",
        paper.highlight && "golden-glow"
      )}
      style={{ height: '18rem' }}>
        <div className="p-4 pb-3 relative z-10 border-b border-gray-100 h-[6rem]">
          <h3 className="text-lg font-heading font-semibold line-clamp-2 mb-1 leading-tight">{paper.title}</h3>
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600 line-clamp-1">{formatAuthors(paper.authors)}</p>
            {formattedDate && (
              <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                {formattedDate}
              </span>
            )}
          </div>
        </div>
        <div className="relative flex-1 w-full flex items-center justify-center z-10" style={{height: "calc(100% - 6rem)"}}>
          <Image
            src={paper.thumbnail_url || "/placeholder.svg"}
            alt={paper.title}
            fill
            className="object-contain p-2"
            onError={handleImageError}
          />
        </div>
      </div>
    )
  }

  return (
    <Link href={`/paper/${paper.uid}`}>
      <div
        className={cn(
          "bg-white rounded-lg border border-gray-100 overflow-hidden transition-all duration-300 relative flex flex-col",
          isHovered ? "shadow-blue-400 shadow-lg z-20" : "shadow-sm",
          isGrayedOut ? "opacity-50" : "opacity-100",
          paper.highlight && "golden-glow"
        )}
        style={{ height: isHovered ? 'auto' : '18rem' }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* Title section */}
        <div className={cn(
          "p-4 pb-3 relative z-10 border-b border-gray-100 transition-all duration-300",
          isHovered ? "min-h-[6rem]" : "h-[6rem]"
        )}>
          <h3 className={cn(
            "text-lg font-heading font-semibold transition-all duration-300 mb-1 leading-tight",
            isHovered ? "" : "line-clamp-2"
          )}>{paper.title}</h3>
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600 line-clamp-1">{formatAuthors(paper.authors)}</p>
            {formattedDate && (
              <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                {formattedDate}
              </span>
            )}
          </div>
        </div>
        
        {/* Card body */}
        <div className="flex-1 flex flex-col transition-all duration-300 relative">
          {/* Image section - always visible but smaller when hovered */}
          <div className={cn(
            "relative transition-all duration-300",
            isHovered ? "h-48" : "flex-1"
          )}>
            <Image
              src={paper.thumbnail_url || "/placeholder.svg"}
              alt={paper.title}
              fill
              className="object-contain p-2"
              onError={handleImageError}
            />
          </div>
          
          {/* Text content section - only visible when hovered */}
          {isHovered && (
            <div className="flex-1 bg-white text-gray-800 overflow-hidden border-t border-gray-100 relative">
              <div 
                ref={contentRef}
                className="p-4 h-full overflow-y-auto scrollbar-hide"
                onScroll={handleScroll}
              >
                <p className="text-sm">{paper.tldr}</p>
              </div>
              
              {/* Top shadow for scroll indication */}
              {showTopShadow && (
                <div className="absolute top-0 left-0 right-0 h-6 bg-gradient-to-b from-white to-transparent pointer-events-none z-10" />
              )}
              
              {/* Bottom shadow for scroll indication */}
              {showBottomShadow && (
                <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-white to-transparent pointer-events-none z-10" />
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

