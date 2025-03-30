"use client"

import { useEffect, useState, useRef, useCallback } from "react"

interface TOCItem {
  id: string
  text: string
  level: number
  offsetTop?: number
}

interface TableOfContentsProps {
  className?: string
}

// Debounce helper function
function debounce<T extends (...args: any[]) => void>(func: T, wait: number): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  
  return function(...args: Parameters<T>) {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export default function TableOfContents({ className = "" }: TableOfContentsProps) {
  const [activeIds, setActiveIds] = useState<Set<string>>(new Set())
  const [tocItems, setTocItems] = useState<TOCItem[]>([])
  const lastScrollY = useRef(0)
  const scrollingDirection = useRef<'up' | 'down'>('down')
  const lastActiveHeadingRef = useRef<string | null>(null)
  const headingUpdateCooldown = useRef(false)
  const isScrolling = useRef(false)
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Extract headings and set up intersection observer on mount
  useEffect(() => {
    // Get all headings h2 and h3 from the article
    const article = document.querySelector("article")
    if (!article) return

    // Function to determine scroll direction
    const updateScrollDirection = () => {
      const currentScrollY = window.scrollY
      if (currentScrollY > lastScrollY.current) {
        scrollingDirection.current = 'down'
      } else if (currentScrollY < lastScrollY.current) {
        scrollingDirection.current = 'up'
      }
      lastScrollY.current = currentScrollY
    }

    // Track scroll activity with debouncing
    const handleScroll = () => {
      updateScrollDirection()
      
      // Set scrolling flag
      isScrolling.current = true;
      
      // Clear any existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      
      // Set a timeout to determine when scrolling stops
      scrollTimeoutRef.current = setTimeout(() => {
        isScrolling.current = false;
        
        // Recheck nearest heading when scrolling stops
        if (activeIds.size === 0) {
          const nearestHeading = findNearestHeading();
          if (nearestHeading && !headingUpdateCooldown.current) {
            setActiveIds(new Set([nearestHeading]));
            lastActiveHeadingRef.current = nearestHeading;
            
            // Set cooldown to prevent oscillation
            setCooldown();
          }
        }
      }, 150); // Detect scroll stop after 150ms of inactivity
    };
    
    // Create debounced scroll handler - only process every 50ms during active scrolling
    const debouncedScrollHandler = debounce(handleScroll, 50);
    
    // Add scroll listener
    window.addEventListener('scroll', debouncedScrollHandler, { passive: true });
    
    // Set cooldown helper function
    const setCooldown = () => {
      headingUpdateCooldown.current = true;
      setTimeout(() => {
        headingUpdateCooldown.current = false;
      }, 300); // 300ms cooldown before allowing another heading change
    };
    
    // Find all headings in the article content
    const headings = Array.from(article.querySelectorAll("h2, h3"))
      .filter(el => el.id || el.textContent) // Only include headings with ID or text content
      .filter(el => {
        // Exclude elements with data-toc-exclude attribute
        return !el.hasAttribute('data-toc-exclude')
      })
    
    // Generate TOC items
    const items: TOCItem[] = headings.map(heading => {
      // If the heading doesn't have an id, create one from its text content
      if (!heading.id && heading.textContent) {
        const id = heading.textContent
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/(^-|-$)/g, "")
        
        heading.id = id
      }
      
      return {
        id: heading.id,
        text: heading.textContent || "",
        level: heading.tagName.toLowerCase() === "h2" ? 2 : 3,
        offsetTop: heading.getBoundingClientRect().top + window.scrollY
      }
    })
    
    setTocItems(items)
    
    // Find nearest heading when none is visible
    const findNearestHeading = () => {
      // If we're in cooldown, don't change the heading
      if (headingUpdateCooldown.current) {
        return lastActiveHeadingRef.current;
      }
      
      const scrollY = window.scrollY
      
      // First check if we're in an intersection area (30% from top)
      const viewportHeight = window.innerHeight
      const threshold = viewportHeight * 0.3
      
      // If we're scrolling down, find the next heading
      if (scrollingDirection.current === 'down') {
        for (const item of items) {
          if (item.offsetTop && item.offsetTop > scrollY && item.offsetTop < scrollY + threshold) {
            return item.id
          }
        }
      }
      
      // Find the closest heading above current scroll position
      let closestHeading = null
      let closestDistance = Infinity
      
      for (const item of items) {
        if (item.offsetTop && item.offsetTop <= scrollY) {
          const distance = scrollY - item.offsetTop
          if (distance < closestDistance) {
            closestDistance = distance
            closestHeading = item.id
          }
        }
      }
      
      return closestHeading
    }
    
    // Set up intersection observer to track which headings are in view
    const observer = new IntersectionObserver(
      (entries) => {
        // If in cooldown, don't process intersection changes
        if (headingUpdateCooldown.current) return;
        
        let hasVisibleHeadings = false
        let shouldUpdateActiveIds = false
        const newActiveIds = new Set(activeIds)
        
        // Update active IDs based on what's visible
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            hasVisibleHeadings = true
            if (!newActiveIds.has(entry.target.id)) {
              newActiveIds.add(entry.target.id)
              shouldUpdateActiveIds = true
            }
            lastActiveHeadingRef.current = entry.target.id
          } else if (newActiveIds.has(entry.target.id)) {
            newActiveIds.delete(entry.target.id)
            shouldUpdateActiveIds = true
          }
        })
        
        // Only update state if there are actual changes
        if (shouldUpdateActiveIds) {
          setActiveIds(newActiveIds)
          setCooldown(); // Set cooldown after updating
        }
        
        // If no headings are visible and we're not actively scrolling, find the nearest one
        if (!hasVisibleHeadings && entries.length > 0 && !isScrolling.current) {
          const nearestHeading = findNearestHeading()
          if (nearestHeading && lastActiveHeadingRef.current !== nearestHeading) {
            setActiveIds(new Set([nearestHeading]))
            lastActiveHeadingRef.current = nearestHeading
            setCooldown(); // Set cooldown after updating
          }
        }
      },
      {
        rootMargin: "-5% 0px -70% 0px", // Consider element as visible when in the top 30% of viewport
        threshold: [0.1, 0.5]
      }
    )
    
    // Observe all heading elements
    headings.forEach(heading => {
      observer.observe(heading)
    })
    
    // Initial check for active heading
    const nearestHeading = findNearestHeading()
    if (nearestHeading) {
      setActiveIds(new Set([nearestHeading]))
      lastActiveHeadingRef.current = nearestHeading
    }
    
    return () => {
      window.removeEventListener('scroll', debouncedScrollHandler)
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      headings.forEach(heading => {
        observer.unobserve(heading)
      })
    }
  }, [])
  
  // Scroll to section when TOC item is clicked
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      // Smooth scroll to the element
      window.scrollTo({
        top: element.offsetTop - 20,
        behavior: "smooth"
      })
      
      // Highlight the item and set cooldown to prevent oscillation
      setActiveIds(new Set([id]))
      lastActiveHeadingRef.current = id
      headingUpdateCooldown.current = true;
      setTimeout(() => {
        headingUpdateCooldown.current = false;
      }, 800); // Longer cooldown after manual click
    }
  }
  
  if (tocItems.length === 0) return null
  
  return (
    <nav className={`toc ${className}`}>
      <style jsx>{`
        .toc-active {
          box-shadow: 0 0 6px 1px rgba(66, 153, 225, 0.4), 0 0 3px 0px rgba(99, 102, 241, 0.3);
          border-left: 2px solid rgba(66, 153, 225, 0.8);
          color: rgb(29, 78, 216) !important;
        }
      `}</style>
      <h3 className="text-base font-semibold mb-4 text-gray-700 border-b border-gray-200 pb-2">Table of Contents</h3>
      <ul className="space-y-1.5">
        {tocItems.map((item) => {
          const isActive = activeIds.has(item.id)
          return (
            <li 
              key={item.id}
              className={`toc-item level-${item.level} text-sm transition-colors duration-200`}
            >
              <button
                onClick={() => scrollToSection(item.id)}
                className={`block text-left w-full py-1.5 px-2 rounded-md transition-all
                  ${item.level === 3 ? "pl-5" : ""} 
                  ${isActive 
                    ? "font-medium toc-active" 
                    : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"}`}
              >
                {item.text}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
} 