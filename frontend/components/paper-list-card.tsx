"use client";

import { Badge } from "@/components/ui/badge";
import { highlightMatches } from "@/lib/search";
import type { PaperSummary } from "@/lib/types";
import { cn, formatAuthors, formatDateFriendly } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  MouseEvent,
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

// Reuse the same HoverContext from PaperCard to maintain consistent behavior
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
    <HoverContext.Provider
      value={{ hoveredId, animatingId, setHoveredId, setAnimatingId }}
    >
      {children}
    </HoverContext.Provider>
  );
}

interface PaperListCardProps {
  paper: PaperSummary;
}

export function PaperListCard({ paper }: PaperListCardProps) {
  const router = useRouter();
  const [isHovered, setIsHovered] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [imageError, setImageError] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const searchParams = useSearchParams();
  const searchQuery = searchParams ? searchParams.get("q") || "" : "";
  const highlightFilter = searchParams
    ? searchParams.get("highlight") === "true"
    : false;

  // Get hover context if available (will be undefined if not wrapped in provider)
  const hoverContext = useContext(HoverContext);

  // Format the date directly here with compact option
  const formattedDate = paper.submitted_date
    ? formatDateFriendly(paper.submitted_date, true)
    : "";

  // Check if device is mobile
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768); // Standard mobile breakpoint
    };

    // Initial check
    checkIfMobile();
    setIsMounted(true);

    // Add resize listener
    window.addEventListener("resize", checkIfMobile);

    // Cleanup
    return () => {
      window.removeEventListener("resize", checkIfMobile);
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  // Handle image error
  const handleImageError = () => {
    setImageError(true);
  };

  // Handle mouse enter/leave with delay and animation (for desktop only)
  const handleMouseEnter = () => {
    if (isMobile) return;

    // Start animation immediately
    setIsAnimating(true);
    if (hoverContext) {
      hoverContext.setAnimatingId(paper.uid);
    }

    // Start timer to set hover state after delay
    hoverTimeoutRef.current = setTimeout(() => {
      setIsHovered(true);
      if (hoverContext) {
        hoverContext.setHoveredId(paper.uid);
      }
    }, 200); // 200ms delay (shorter than grid view for better UX)
  };

  const handleMouseLeave = () => {
    if (isMobile) return;

    // Clear the timeout if mouse leaves before delay completes
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }

    // Reset states
    setIsAnimating(false);
    setIsHovered(false);
    if (hoverContext) {
      hoverContext.setAnimatingId(null);
      hoverContext.setHoveredId(null);
    }
  };

  // Handle card click for mobile
  const handleCardClick = (e: MouseEvent) => {
    if (!isMobile) return;
    e.preventDefault(); // Prevent default Link behavior
    router.push(`/paper/${paper.uid}`);
  };

  // Determine card states based on global context
  const isActive =
    paper.uid === hoverContext?.hoveredId ||
    paper.uid === hoverContext?.animatingId;
  const shouldFadeOut =
    (hoverContext?.hoveredId !== null || hoverContext?.animatingId !== null) &&
    !isActive;

  // Get summary text, falling back to abstract if tldr is not available
  const summaryText = paper.tldr || paper.abstract || "";

  // Create highlighted versions of title, authors, and summary if search is active
  const title = searchQuery ? (
    <span
      dangerouslySetInnerHTML={{
        __html: highlightMatches(paper.title, searchQuery),
      }}
    />
  ) : (
    paper.title
  );

  const authors = searchQuery ? (
    <span
      dangerouslySetInnerHTML={{
        __html: highlightMatches(formatAuthors(paper.authors), searchQuery),
      }}
    />
  ) : (
    formatAuthors(paper.authors)
  );

  const summary = searchQuery ? (
    <span
      dangerouslySetInnerHTML={{
        __html: highlightMatches(summaryText, searchQuery),
      }}
    />
  ) : (
    summaryText
  );

  // Condition to check if we should show the summary instead of the image
  const hasNoThumbnail = !paper.thumbnail_url || imageError;

  if (!isMounted) {
    return (
      <div
        className={cn(
          "bg-white card-radius shadow-sm border border-gray-100 overflow-hidden relative flex"
        )}
        style={{ height: "12rem" }}
      >
        {/* Badge for highlighted papers */}
        {paper.highlight && !highlightFilter && (
          <div className="absolute bottom-2 right-2 z-20">
            <Badge className="bg-blue-500/80 hover:bg-blue-500/90 text-white">
              Highlighted
            </Badge>
          </div>
        )}
        
        {/* Layout with or without thumbnail */}
        {!hasNoThumbnail ? (
          <>
            {/* Thumbnail area - 40% width when thumbnail exists */}
            <div className="w-2/5 relative border-r border-gray-100">
              <div className="relative w-full h-full">
                <Image
                  src={paper.thumbnail_url || "/placeholder.svg"}
                  alt={paper.title}
                  fill
                  className="object-contain p-2"
                  onError={handleImageError}
                />
              </div>
            </div>
            
            {/* Content area - 60% width when thumbnail exists */}
            <div className="w-3/5 relative">
              <div 
                className={`absolute inset-0 p-4 ${isHovered ? 'overflow-y-auto scrollbar-hide' : 'overflow-hidden'}`}
              >
                <h3 className={`text-lg font-heading font-semibold mb-1 leading-tight ${!isHovered ? 'line-clamp-2' : ''}`}>
                  {title}
                </h3>
                <div className="flex justify-between items-center mb-2">
                  <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-1' : ''}`}>{authors}</p>
                  {formattedDate && (
                    <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                      {formattedDate}
                    </span>
                  )}
                </div>
                
                <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-3' : ''}`}>{summary}</p>
              </div>
              
              {isHovered && (
                <>
                  <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-white to-transparent pointer-events-none opacity-75 z-10" />
                  <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-white to-transparent pointer-events-none opacity-75 z-10" />
                </>
              )}
            </div>
          </>
        ) : (
          /* Full width content when no thumbnail */
          <div className="w-full relative">
            <div 
              className={`absolute inset-0 p-4 ${isHovered ? 'overflow-y-auto scrollbar-hide' : 'overflow-hidden'}`}
            >
              <h3 className={`text-lg font-heading font-semibold mb-1 leading-tight ${!isHovered ? 'line-clamp-2' : ''}`}>
                {title}
              </h3>
              <div className="flex justify-between items-center mb-2">
                <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-1' : ''}`}>{authors}</p>
                {formattedDate && (
                  <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                    {formattedDate}
                  </span>
                )}
              </div>
              
              <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-5' : ''}`}>{summary}</p>
            </div>
            
            {isHovered && (
              <>
                <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-white to-transparent pointer-events-none opacity-75 z-10" />
                <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-white to-transparent pointer-events-none opacity-75 z-10" />
              </>
            )}
          </div>
        )}
      </div>
    );
  }

  // Create the card content element that will be used in both mobile and desktop views
  const cardContent = (
    <div
      ref={cardRef}
      className={cn(
        "bg-white card-radius overflow-hidden relative flex",
        // Border and shadow animation states
        isHovered || isAnimating
          ? "border border-blue-400"
          : "border border-gray-100",
        // Shadow animation states
        isHovered
          ? "card-glow z-20"
          : isAnimating
          ? "animate-grow-shadow z-10"
          : "shadow-sm",
        // Fade animation for background cards
        shouldFadeOut ? "animate-fade-out" : "",
        // Mobile tap indicator
        isMobile ? "tap-effect" : ""
      )}
      style={{
        height: "12rem",
        transition:
          "border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Badge for highlighted papers */}
      {paper.highlight && !highlightFilter && (
        <div className="absolute bottom-2 right-2 z-20">
          <Badge className="bg-blue-500/80 hover:bg-blue-500/90 text-white">
            Highlighted
          </Badge>
        </div>
      )}
      
      {/* Layout with or without thumbnail */}
      {!hasNoThumbnail ? (
        <>
          {/* Thumbnail area - 40% width when thumbnail exists */}
          <div className="w-2/5 relative border-r border-gray-100">
            <div className="relative w-full h-full">
              <Image
                src={paper.thumbnail_url || "/placeholder.svg"}
                alt={paper.title}
                fill
                className="object-contain p-2"
                onError={handleImageError}
              />
            </div>
          </div>
          
          {/* Content area - 60% width when thumbnail exists */}
          <div className="w-3/5 relative">
            <div 
              className={`absolute inset-0 p-4 ${isHovered ? 'overflow-y-auto scrollbar-hide' : 'overflow-hidden'}`}
            >
              <h3 className={`text-lg font-heading font-semibold mb-1 leading-tight ${!isHovered ? 'line-clamp-2' : ''}`}>
                {title}
              </h3>
              <div className="flex justify-between items-center mb-2">
                <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-1' : ''}`}>{authors}</p>
                {formattedDate && (
                  <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                    {formattedDate}
                  </span>
                )}
              </div>
              
              <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-3' : ''}`}>{summary}</p>
            </div>
            
            {isHovered && (
              <>
                <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-white to-transparent pointer-events-none opacity-75 z-10" />
                <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-white to-transparent pointer-events-none opacity-75 z-10" />
              </>
            )}
          </div>
        </>
      ) : (
        /* Full width content when no thumbnail */
        <div className="w-full relative">
          <div 
            className={`absolute inset-0 p-4 ${isHovered ? 'overflow-y-auto scrollbar-hide' : 'overflow-hidden'}`}
          >
            <h3 className={`text-lg font-heading font-semibold mb-1 leading-tight ${!isHovered ? 'line-clamp-2' : ''}`}>
              {title}
            </h3>
            <div className="flex justify-between items-center mb-2">
              <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-1' : ''}`}>{authors}</p>
              {formattedDate && (
                <span className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                  {formattedDate}
                </span>
              )}
            </div>
            
            <p className={`text-sm text-gray-600 ${!isHovered ? 'line-clamp-5' : ''}`}>{summary}</p>
          </div>
          
          {isHovered && (
            <>
              <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-white to-transparent pointer-events-none opacity-75 z-10" />
              <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-white to-transparent pointer-events-none opacity-75 z-10" />
            </>
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
          animation: grow-shadow 0.2s ease-in-out forwards;
        }

        .animate-fade-out {
          animation: fade-out 0.2s ease-in-out forwards;
        }

        /* Mobile tap effect */
        .tap-effect:active {
          transform: scale(0.98);
          transition: transform 0.1s;
        }
        
        /* Hide scrollbar for all browsers */
        .scrollbar-hide {
          -ms-overflow-style: none;  /* IE and Edge */
          scrollbar-width: none;  /* Firefox */
        }
        
        /* Hide scrollbar for Chrome, Safari and Opera */
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );

  // Render different wrappers based on device type
  return isMobile ? (
    // For mobile: div with click handler
    <div onClick={handleCardClick}>{cardContent}</div>
  ) : (
    // For desktop: Link component
    <Link href={`/paper/${paper.uid}`} passHref prefetch>
      {cardContent}
    </Link>
  );
} 