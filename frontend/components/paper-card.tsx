"use client"

import type { PaperSummary } from "@/lib/types"
import Link from "next/link"
import { useState, useEffect, useRef, createContext, useContext } from "react"
import Image from "next/image"
import { formatAuthors, formatDateFriendly, cn } from "@/lib/utils"
import { useSearchParams } from "next/navigation"
import { highlightMatches } from "@/lib/search"
import { Badge } from "@/components/ui/badge"

// Create context for tracking global hover state
const HoverContext = createContext<{
  hoveredId: string | null;
  animatingId: string | null;
  setHoveredId: (id: string | null) => void;
  setAnimatingId: (id: string | null) => void;
}>({
  hoveredId: null,
  animatingId: null,
  setHoveredId: () => {},
  setAnimatingId: () => {},
});

export function PaperCardProvider({ children }: { children: React.ReactNode }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [animatingId, setAnimatingId] = useState<string | null>(null);
  
  return (
    <HoverContext.Provider value={{ hoveredId, animatingId, setHoveredId, setAnimatingId }}>
      {children}
    </HoverContext.Provider>
  );
}

interface PaperCardProps {
  paper: PaperSummary
}

export default function PaperCard({ paper }: PaperCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)
  const [isMounted, setIsMounted] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [isInViewport, setIsInViewport] = useState(false)
  const [showTopShadow, setShowTopShadow] = useState(false)
  const [showBottomShadow, setShowBottomShadow] = useState(true)
  const [imageError, setImageError] = useState(false)
  const contentRef = useRef<HTMLDivElement>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const viewportTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const searchParams = useSearchParams()
  const searchQuery = searchParams ? searchParams.get('q') || '' : ''
  const highlightFilter = searchParams ? searchParams.get('highlight') === 'true' : false
  
  // Get hover context if available (will be undefined if not wrapped in provider)
  const hoverContext = useContext(HoverContext);

  // Format the date directly here with compact option
  const formattedDate = paper.submitted_date ? formatDateFriendly(paper.submitted_date, true) : "";
  
  // Check if device is mobile
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768); // Standard mobile breakpoint
    };
    
    // Initial check
    checkIfMobile();
    setIsMounted(true);
    
    // Add resize listener
    window.addEventListener('resize', checkIfMobile);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', checkIfMobile);
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
      if (viewportTimeoutRef.current) {
        clearTimeout(viewportTimeoutRef.current);
      }
    };
  }, []);
  
  // Set up intersection observer for mobile
  useEffect(() => {
    if (!isMobile || !cardRef.current || !isMounted) return;
    
    const options = {
      root: null, // Use viewport
      rootMargin: '0px',
      threshold: 0.9 // Card must be 90% visible
    };
    
    const handleIntersection = (entries: IntersectionObserverEntry[]) => {
      const entry = entries[0];
      
      // Check if this card is fully visible in the viewport
      if (entry.isIntersecting) {
        setIsInViewport(true);
        
        // Start a timer - activate after 2 seconds on mobile
        viewportTimeoutRef.current = setTimeout(() => {
          if (!isHovered) {
            setIsAnimating(true);
            if (hoverContext) {
              hoverContext.setAnimatingId(paper.uid);
            }
            
            // After animation, show content
            hoverTimeoutRef.current = setTimeout(() => {
              setIsHovered(true);
              if (hoverContext) {
                hoverContext.setHoveredId(paper.uid);
              }
            }, 1000);
          }
        }, 2000);
      } else {
        setIsInViewport(false);
        
        // Clear timers if card scrolls out of view
        if (viewportTimeoutRef.current) {
          clearTimeout(viewportTimeoutRef.current);
          viewportTimeoutRef.current = null;
        }
        
        if (hoverTimeoutRef.current) {
          clearTimeout(hoverTimeoutRef.current);
          hoverTimeoutRef.current = null;
        }
        
        // Reset state if card scrolls away
        setIsAnimating(false);
        setIsHovered(false);
        if (hoverContext) {
          hoverContext.setAnimatingId(null);
          hoverContext.setHoveredId(null);
        }
      }
    };
    
    const observer = new IntersectionObserver(handleIntersection, options);
    observer.observe(cardRef.current);
    
    return () => {
      observer.disconnect();
    };
  }, [isMobile, isMounted, paper.uid, isHovered, hoverContext]);

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

  // Handle mouse enter/leave with delay and animation
  const handleMouseEnter = () => {
    // Skip hover handling on mobile as we're using intersection observer
    if (isMobile) return;
    
    // Start animation immediately
    setIsAnimating(true)
    if (hoverContext) {
      hoverContext.setAnimatingId(paper.uid)
    }
    
    // Start timer to set hover state after delay
    hoverTimeoutRef.current = setTimeout(() => {
      setIsHovered(true)
      if (hoverContext) {
        hoverContext.setHoveredId(paper.uid)
      }
    }, 1000) // 1 second delay
  }

  const handleMouseLeave = () => {
    // Skip hover handling on mobile as we're using intersection observer
    if (isMobile) return;
    
    // Clear the timeout if mouse leaves before delay completes
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
      hoverTimeoutRef.current = null
    }
    
    // Reset states
    setIsAnimating(false)
    setIsHovered(false)
    if (hoverContext) {
      hoverContext.setAnimatingId(null)
      hoverContext.setHoveredId(null)
    }
  }

  // Determine card states based on global context
  const isActive = paper.uid === hoverContext?.hoveredId || paper.uid === hoverContext?.animatingId;
  const shouldFadeOut = (hoverContext?.hoveredId !== null || hoverContext?.animatingId !== null) && !isActive;

  // Create highlighted versions of title, authors, and tldr if search is active
  const title = searchQuery 
    ? <span dangerouslySetInnerHTML={{ __html: highlightMatches(paper.title, searchQuery) }} />
    : paper.title;
    
  const authors = searchQuery
    ? <span dangerouslySetInnerHTML={{ __html: highlightMatches(formatAuthors(paper.authors), searchQuery) }} />
    : formatAuthors(paper.authors);
    
  const tldr = searchQuery
    ? <span dangerouslySetInnerHTML={{ __html: highlightMatches(paper.tldr, searchQuery) }} />
    : paper.tldr;

  if (!isMounted) {
    return (
      <div className={cn(
        "bg-white card-radius shadow-sm border border-gray-100 overflow-hidden relative",
      )}
      style={{ height: '18rem' }}>
        {/* Badge for highlighted papers */}
        {paper.highlight && !highlightFilter && (
          <div className="absolute bottom-2 right-2 z-20">
            <Badge className="bg-blue-500/80 hover:bg-blue-500/90 text-white">Highlighted</Badge>
          </div>
        )}
        <div className="p-4 pb-3 relative z-10 border-b border-gray-100 h-[6rem]">
          <h3 className="text-lg font-heading font-semibold line-clamp-2 mb-1 leading-tight">{title}</h3>
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600 line-clamp-1">{authors}</p>
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
    <Link href={`/paper/${paper.uid}`} passHref>
      <div
        ref={cardRef}
        className={cn(
          "bg-white card-radius overflow-hidden relative",
          // Outline when in viewport on mobile
          isMobile && isInViewport && !isAnimating && !isHovered ? "outline outline-1 outline-blue-200" : "",
          // Border and shadow animation states
          (isHovered || isAnimating) ? "border border-blue-400" : "border border-gray-100",
          // Shadow animation states
          isHovered ? "card-glow z-20" : 
            isAnimating ? "animate-grow-shadow z-10" : "shadow-sm",
          // Fade animation for background cards
          shouldFadeOut ? "animate-fade-out" : "",
        )}
        style={{ 
          height: '18rem',
          transition: 'border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out'
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {/* Badge for highlighted papers - only shown when not hovered and not filtered */}
        {paper.highlight && !isHovered && !highlightFilter && (
          <div className="absolute bottom-2 right-2 z-30">
            <Badge className="bg-blue-500/80 hover:bg-blue-500/90 text-white">Highlighted</Badge>
          </div>
        )}
        
        {!isHovered && (
          <>
            {/* Non-hovered state: Title section with truncated title */}
            <div className="p-4 pb-3 relative z-10 border-b border-gray-100 h-[6rem]">
              <h3 className="text-lg font-heading font-semibold line-clamp-2 mb-1 leading-tight">{title}</h3>
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600 line-clamp-1">{authors}</p>
                {formattedDate && (
                  <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                    {formattedDate}
                  </span>
                )}
              </div>
            </div>
            
            {/* Image shown when not hovered */}
            <div className="relative w-full h-[12rem] flex items-center justify-center">
              <Image
                src={paper.thumbnail_url || "/placeholder.svg"}
                alt={paper.title}
                fill
                className="object-contain p-2"
                onError={handleImageError}
              />
            </div>
          </>
        )}
        
        {/* Scrollable content shown when hovered */}
        {isHovered && (
          <div className="relative h-full w-full overflow-hidden">
            <div 
              ref={contentRef}
              className="absolute inset-0 p-4 overflow-y-auto scrollbar-hide bg-white"
              onScroll={handleScroll}
            >
              {/* Full title */}
              <h3 className="text-lg font-heading font-semibold mb-1 leading-tight">{title}</h3>
              
              {/* Authors and date */}
              <div className="flex justify-between items-center mb-3">
                <p className="text-sm text-gray-600">{authors}</p>
                {formattedDate && (
                  <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                    {formattedDate}
                  </span>
                )}
              </div>
              
              {/* Divider */}
              <div className="border-t border-blue-100 mb-3"></div>
              
              {/* Summary */}
              <p className="text-sm">{tldr}</p>
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

        {/* Add animation keyframes for growing shadow */}
        <style jsx global>{`
          /* Define the shared glow effect to ensure consistency */
          .card-glow {
            box-shadow: 0 10px 25px -3px rgba(96, 165, 250, 0.7), 
                        0 0 10px 2px rgba(96, 165, 250, 0.4);
          }
          
          @keyframes grow-shadow {
            0% {
              box-shadow: 0 1px 3px rgba(96, 165, 250, 0.1);
            }
            100% {
              /* Use exactly the same shadow as card-glow for a smooth transition */
              box-shadow: 0 10px 25px -3px rgba(96, 165, 250, 0.7), 
                          0 0 10px 2px rgba(96, 165, 250, 0.4);
            }
          }
          
          @keyframes fade-out {
            0% {
              opacity: 1;
            }
            100% {
              opacity: 0.5;
            }
          }
          
          .animate-grow-shadow {
            animation: grow-shadow 1s ease-in-out forwards;
          }
          
          .animate-fade-out {
            animation: fade-out 1s ease-in-out forwards;
          }
        `}</style>
      </div>
    </Link>
  )
}

